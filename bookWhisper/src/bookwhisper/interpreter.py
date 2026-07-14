"""DeepSeek 解读模块。

调用 DeepSeek API 解读书籍文本：
- 生成整书摘要
- 逐块解读章节内容
- 内置指数退避重试
- 通过 CheckpointManager 实现断点续传
"""

from __future__ import annotations

import logging
import time
from typing import Any

from openai import OpenAI

from bookwhisper.checkpoint import ChapterResult, CheckpointManager
from bookwhisper.config import AppConfig, DeepSeekConfig
from bookwhisper.prompts import REVIEW_PROMPT, RULES_REMINDER, SUMMARY_PROMPT, SYSTEM_PROMPT
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

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable


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
    ) -> None:
        self._config = config
        self._checkpoint = checkpoint
        self._client = OpenAI(
            api_key=config.deepseek.api_key,
            base_url=config.deepseek.base_url,
        )

    # ---- 整书摘要 ----

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

    def generate_summary_with_retry(
        self,
        front_matter: str,
        max_retries: int = 3,
    ) -> str:
        """带重试的整书摘要生成。

        优先从 checkpoint 恢复；若无缓存则调用 API 并在失败时重试。

        Args:
            front_matter: 前辅文纯文本。
            max_retries: 最大重试次数。

        Returns:
            整书摘要。

        Raises:
            InterpretError: 所有重试均失败。
        """
        # 尝试从 checkpoint 恢复
        if self._checkpoint is not None:
            cached = self._checkpoint.get_book_summary()
            if cached:
                logger.info("从 checkpoint 恢复整书摘要")
                return cached

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return self.generate_summary(front_matter)
            except InterpretError as e:
                last_error = e
                if not e.retryable:
                    raise
                if attempt < max_retries:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "摘要生成失败（%d/%d），%d 秒后重试: %s",
                        attempt + 1,
                        max_retries,
                        wait,
                        e.message,
                    )
                    time.sleep(wait)
                else:
                    logger.error("摘要生成失败，已达最大重试次数: %s", e.message)

        raise InterpretError(
            f"摘要生成失败，已重试 {max_retries} 次: {last_error}"
        )

    # ---- 章节解读 ----

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
        user_content = self._build_user_content(section, book_summary, previous_text)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
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

        # 标记完成
        if self._checkpoint is not None:
            self._checkpoint.mark_done(section_id, result)

        return result

    # ---- 二次全文重写 ----

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

    # ---- 重试逻辑 ----

    def interpret_section_with_retry(
        self,
        section: Section,
        book_summary: str,
        max_retries: int = 3,
        previous_text: str = "",
    ) -> ChapterResult:
        """带重试的章节解读。

        Args:
            section: 要解读的章节块。
            book_summary: 整书摘要。
            max_retries: 最大重试次数。
            previous_text: 同一章内上一块的解读结果，用于保持解读连贯性。

        Returns:
            ChapterResult 解读结果。

        Raises:
            InterpretError: 所有重试均失败。
        """
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return self.interpret_section(section, book_summary, previous_text)
            except InterpretError as e:
                last_error = e
                if not e.retryable:
                    raise
                if attempt < max_retries:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "解读失败（%d/%d），%d 秒后重试: %s",
                        attempt + 1,
                        max_retries,
                        wait,
                        e.message,
                    )
                    if self._checkpoint is not None:
                        self._checkpoint.mark_failed(section.id, str(e))
                    time.sleep(wait)
                else:
                    logger.error("解读失败，已达最大重试次数: %s", e.message)
                    if self._checkpoint is not None:
                        self._checkpoint.mark_failed(section.id, str(e))

        raise InterpretError(
            f"解读 {section.id} 失败，已重试 {max_retries} 次: {last_error}"
        )

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

        try:
            response = self._client.chat.completions.create(
                model=self._config.deepseek.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if content is None:
                raise InterpretError("API 返回空内容", retryable=True)
            return content

        except Exception as e:
            error_name = type(e).__name__
            is_retryable = any(
                retry_name in error_name for retry_name in _RETRYABLE_ERRORS
            )
            raise InterpretError(f"{error_name}: {e}", retryable=is_retryable) from e

    @staticmethod
    def _build_user_content(
        section: Section, book_summary: str, previous_text: str = ""
    ) -> str:
        """构建发送给 LLM 的用户消息。

        包含：前文回顾 + 整书摘要 + 章节上下文标签 + 章节文本。
        """
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
