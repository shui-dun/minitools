"""DeepSeek 解读模块。

调用 DeepSeek API 解读书籍文本：
- 生成整书摘要
- 逐块解读章节内容
- 内置指数退避重试
- 通过 CheckpointManager 实现断点续传
"""

from __future__ import annotations

import functools
import json
import logging
import sys
import time
from typing import Any

from openai import OpenAI

from bookwhisper.checkpoint import ChapterResult, CheckpointManager
from bookwhisper.config import AppConfig, DeepSeekConfig
from bookwhisper.prompts import (
    NOVEL_RULES_REMINDER,
    NOVEL_SYSTEM_PROMPT,
    REVIEW_PROMPT,
    RULES_REMINDER,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)
from bookwhisper.splitter import Section

logger = logging.getLogger(__name__)

# 可重试的错误类型
_RETRYABLE_ERRORS = (
    "ConnectionError",
    "ConnectionResetError",
    "Timeout",
    "APITimeoutError",
    "APIConnectionError",
    "RateLimitError",
    "ServiceUnavailableError",
    "InternalServerError",
)


class InterpretError(Exception):
    """解读失败。"""

    def __init__(
        self,
        message: str,
        retryable: bool = False,
        empty_fallback: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        self.empty_fallback = empty_fallback


def _is_empty_result(result: Any) -> bool:
    """检查返回结果是否为空文本（长度为 0）。"""
    if isinstance(result, str):
        return len(result) == 0
    if isinstance(result, ChapterResult):
        return len(result.interpreted_text) == 0
    return False


def _dump_curl(
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> None:
    """将 API 请求打印为可复制的 curl 命令（输出到 stderr）。"""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    escaped = body.replace("'", "'\\''")
    curl = (
        "curl -s https://api.deepseek.com/chat/completions \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -H 'Authorization: Bearer $DEEPSEEK_API_KEY' \\\n"
        f"  -d '{escaped}'"
    )
    print(f"\n{'=' * 60}\n[VERBOSE] DeepSeek API 请求\n{'=' * 60}", file=sys.stderr)
    print(curl, file=sys.stderr)
    print("=" * 60, file=sys.stderr)


def _dump_response(response: Any) -> None:
    """将 API 响应关键信息打印到 stderr（verbose 模式）。"""
    choice = response.choices[0]
    finish = getattr(choice, "finish_reason", "N/A")
    content = choice.message.content
    content_len = len(content) if content else 0

    print(f"\n{'=' * 60}", file=sys.stderr)
    print("[VERBOSE] DeepSeek API 响应", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"  finish_reason : {finish}", file=sys.stderr)
    print(f"  content length: {content_len}", file=sys.stderr)

    reasoning = getattr(choice.message, "reasoning_content", None)
    if reasoning:
        print(f"  reasoning_content ({len(reasoning)} 字符):", file=sys.stderr)
        print(f"  --- reasoning 开始 ---", file=sys.stderr)
        print(reasoning, file=sys.stderr)
        print(f"  --- reasoning 结束 ---", file=sys.stderr)

    if content:
        print(f"  content (前 200 字): {content[:200]}", file=sys.stderr)
    else:
        print("  content: (空)", file=sys.stderr)
        fields = [f for f in dir(choice.message) if not f.startswith("_")]
        print(f"  message fields: {fields}", file=sys.stderr)

    usage = getattr(response, "usage", None)
    if usage:
        pt = getattr(usage, "prompt_tokens", "?")
        ct = getattr(usage, "completion_tokens", "?")
        tt = getattr(usage, "total_tokens", "?")
        print(f"  usage: prompt={pt}, completion={ct}, total={tt}", file=sys.stderr)

    print("=" * 60, file=sys.stderr)


def retry_on_error(func):
    """指数退避重试装饰器。遇到可重试的 InterpretError 自动重试。

    重试次数从实例的 config.max_retries 读取。
    同时检查返回结果：若输出文本长度为 0，视为失败并重试。
    """

    @functools.wraps(func)
    def wrapper(self: DeepSeekInterpreter, *args: Any, **kwargs: Any) -> Any:
        max_retries = self._config.max_retries
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                result = func(self, *args, **kwargs)
                # 输出文本长度为 0，视作失败，触发重试
                if _is_empty_result(result):
                    raise InterpretError("输出文本长度为 0", retryable=True, empty_fallback=True)
                return result
            except InterpretError as e:
                last_error = e
                if not e.retryable:
                    raise
                # 空内容回退模式：一次空内容就立即抛出，不重试
                if e.empty_fallback and self._config.fallback_to_original_on_empty:
                    raise
                if attempt < max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        "%s 失败（%d/%d），%d 秒后重试: %s",
                        func.__name__,
                        attempt + 1,
                        max_retries,
                        wait,
                        e.message,
                    )
                    time.sleep(wait)
                else:
                    logger.error("%s 已达最大重试次数: %s", func.__name__, e.message)

        raise InterpretError(
            f"{func.__name__} 失败，已重试 {max_retries} 次: {last_error}",
            empty_fallback=(
                isinstance(last_error, InterpretError) and last_error.empty_fallback
            ),
        )

    return wrapper


class DeepSeekInterpreter:
    """DeepSeek API 解读器。

    用法：
        interpreter = DeepSeekInterpreter(config, checkpoint_manager)
        # 生成整书摘要
        summary = interpreter.generate_summary(front_matter_text)
        # 逐块解读
        for section in sections:
            result = interpreter.interpret_section(section, summary)
    """

    def __init__(
        self,
        config: AppConfig,
        checkpoint: CheckpointManager | None = None,
        mode: str = "default",
        verbose: bool = False,
    ) -> None:
        self._config = config
        self._checkpoint = checkpoint
        self._mode = mode
        self._verbose = verbose
        self._system_prompt = SYSTEM_PROMPT if mode != "novel" else NOVEL_SYSTEM_PROMPT
        self._client = OpenAI(
            api_key=config.deepseek.api_key,
            base_url=config.deepseek.base_url,
        )

    # ---- 整书摘要 ----

    @retry_on_error
    def generate_summary(self, front_matter: str) -> str:
        """根据前辅文生成整书摘要。

        优先从 checkpoint 恢复已生成的摘要。

        Args:
            front_matter: 前辅文纯文本（目录 + 前言 + 第一章）。

        Returns:
            整书摘要。
        """
        # 尝试从 checkpoint 恢复
        if self._checkpoint is not None:
            cached = self._checkpoint.get_book_summary()
            if cached:
                logger.info("从 checkpoint 恢复整书摘要")
                return cached

        max_chars = self._config.chunk.book_summary_chars
        prompt = SUMMARY_PROMPT.format(max_chars=max_chars, content=front_matter)

        logger.info("正在生成整书摘要...")
        summary = self._call_api(
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=min(max_chars * 3, 2048),
        )

        # 保存到 checkpoint
        if self._checkpoint is not None:
            self._checkpoint.set_book_summary(summary)

        logger.info("整书摘要生成完成（%d 字）", len(summary))
        return summary

    # ---- 章节解读 ----

    @retry_on_error
    def interpret_section(
        self,
        section: Section,
        book_summary: str,
        previous_text: str = "",
    ) -> ChapterResult:
        """解读单个章节块。

        Args:
            section: 要解读的章节块。
            book_summary: 整书摘要，注入到每次请求的上下文中。
            previous_text: 同一章内上一块的解读结果，用于保持解读连贯性。

        Returns:
            ChapterResult 解读结果。

        Raises:
            InterpretError: 解读失败。
        """
        section_id = section.id
        original_chars = len(section.text)

        logger.info(
            "正在解读 %s（%d 字符）...",
            section.context_label,
            original_chars,
        )

        # 构建消息
        user_content = self._build_user_content(
            section, book_summary, previous_text,
            novel_mode=(self._mode == "novel"),
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_content},
        ]

        interpreted_text = self._call_api(
            messages=messages,
            max_tokens=self._config.deepseek.max_tokens,
        )

        result = ChapterResult(
            chapter_id=section_id,
            original_chars=original_chars,
            interpreted_chars=len(interpreted_text),
            interpreted_text=interpreted_text,
        )

        logger.info(
            "%s 解读完成: %d → %d 字符",
            section.context_label,
            original_chars,
            result.interpreted_chars,
        )

        return result

    # ---- 二次全文重写 ----

    @retry_on_error
    def review_and_refine(self, first_result: str) -> str:
        """对第一轮通俗化结果进行二次全文重写。

        Args:
            first_result: 第一轮通俗化文本。

        Returns:
            重写后的最终文本。
        """
        user_content = REVIEW_PROMPT.format(content=first_result)

        logger.info("正在进行二次全文重写（%d 字）...", len(first_result))
        refined = self._call_api(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=self._config.deepseek.max_tokens,
        )
        logger.info("二次重写完成: %d → %d 字", len(first_result), len(refined))
        return refined

    # ---- 内部方法 ----

    def _call_api(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float | None = None,
    ) -> str:
        """调用 DeepSeek API（OpenAI 兼容）。

        Args:
            messages: 消息列表。
            max_tokens: 最大输出 token 数。
            temperature: 温度参数。

        Returns:
            API 返回的文本。

        Raises:
            InterpretError: API 调用失败。
        """
        if temperature is None:
            temperature = self._config.deepseek.temperature

        if self._verbose:
            _dump_curl(
                self._config.deepseek.model,
                messages,
                temperature,
                max_tokens,
            )

        try:
            response = self._client.chat.completions.create(
                model=self._config.deepseek.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if self._verbose:
                _dump_response(response)

            content = response.choices[0].message.content
            if not content:
                raise InterpretError("API 返回空内容", retryable=True, empty_fallback=True)
            return content

        except InterpretError:
            raise  # 已经是 InterpretError，保留原始 retryable 标记，不重新包装
        except Exception as e:
            error_name = type(e).__name__
            is_retryable = any(
                retry_name in error_name for retry_name in _RETRYABLE_ERRORS
            )
            raise InterpretError(f"{error_name}: {e}", retryable=is_retryable) from e

    @staticmethod
    def _build_user_content(
        section: Section,
        book_summary: str = "",
        previous_text: str = "",
        *,
        novel_mode: bool = False,
    ) -> str:
        """构建发送给 LLM 的用户消息。

        包含：前文回顾 + 整书摘要 + 章节上下文标签 + 章节文本。
        novel 模式下仅包含前文回顾和原文，不含摘要和规则重申。
        """
        if novel_mode:
            parts: list[str] = []
            # 只取上一段末尾 300 字作为衔接上下文，并加标签区分
            if previous_text and len(previous_text) > 300:
                prev_tail = previous_text[-300:]
            elif previous_text:
                # 如果上一段本身就很短（<=300 字），保留原文
                prev_tail = previous_text
            else:
                prev_tail = ""

            if prev_tail:
                parts.append(
                    "【前文末尾】以下是上一段的末尾内容，"
                    "仅供衔接上下文，请勿修改：\n" + prev_tail
                )

            parts.append("请优化以下文本：\n" + section.text)
            parts.append(NOVEL_RULES_REMINDER)
            return "\n\n".join(parts)

        parts: list[str] = []

        if previous_text:
            parts.append(
                f"【前文回顾】\n"
                f"以下是紧接在本段之前的内容，请确保解读的连贯性，"
                f"避免重复解释已经出现过的术语：\n{previous_text}"
            )

        if book_summary:
            parts.append(f"【整书摘要】\n{book_summary}")

        parts.append(f"【当前解读位置】\n{section.context_label}")
        parts.append(f"【原文内容】\n{section.text}")

        # 规则重申放在末尾，对抗 lost-in-the-middle
        parts.append(RULES_REMINDER)

        return "\n\n".join(parts)
