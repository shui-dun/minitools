"""interpreter.py 单元测试（mock DeepSeek API）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookwhisper.checkpoint import CheckpointManager
from bookwhisper.config import AppConfig
from bookwhisper.interpreter import DeepSeekInterpreter, InterpretError
from bookwhisper.splitter import Section


@pytest.fixture
def interpreter_config() -> AppConfig:
    """创建测试用的配置（含 fake API key）。"""
    config = AppConfig()
    config.deepseek.api_key = "sk-test-fake"
    return config


@pytest.fixture
def mock_openai_response():
    """mock OpenAI API 返回。"""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = "这是解读后的文本内容。"
    return mock


@pytest.fixture
def sample_section() -> Section:
    """创建测试用的 Section。"""
    return Section(
        chapter_index=0,
        chapter_title="测试章节",
        section_index=0,
        total_sections=1,
        text="这是一段测试文本。值得注意的是，在某种程度上，这个理论被许多学者所广泛讨论。",
    )


class TestInterpreterSummary:
    """整书摘要测试。"""

    @patch("bookwhisper.interpreter.OpenAI")
    def test_generate_summary(self, mock_openai_cls, interpreter_config, mock_openai_response):
        """生成整书摘要。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        interpreter = DeepSeekInterpreter(interpreter_config)
        summary = interpreter.generate_summary("前言内容测试。")

        assert len(summary) > 0
        assert summary == "这是解读后的文本内容。"

    @patch("bookwhisper.interpreter.OpenAI")
    def test_summary_from_checkpoint(self, mock_openai_cls, interpreter_config, sample_epub_path):
        """从 checkpoint 恢复摘要时不调用 API。"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        cpm = CheckpointManager(sample_epub_path.parent, sample_epub_path)
        cpm.set_book_summary("缓存的摘要")

        interpreter = DeepSeekInterpreter(interpreter_config, cpm)
        summary = interpreter.generate_summary("一些内容")

        # 应从 checkpoint 恢复，不调用 API
        assert summary == "缓存的摘要"
        mock_client.chat.completions.create.assert_not_called()

    @patch("bookwhisper.interpreter.OpenAI")
    def test_generate_summary_with_retry(
        self, mock_openai_cls, interpreter_config, mock_openai_response
    ):
        """generate_summary 内置重试，调用成功。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        interpreter = DeepSeekInterpreter(interpreter_config)
        summary = interpreter.generate_summary("前言内容。")

        assert summary == "这是解读后的文本内容。"

    @patch("bookwhisper.interpreter.OpenAI")
    def test_generate_summary_retry_on_error(
        self, mock_openai_cls, interpreter_config
    ):
        """摘要生成失败应重试。"""
        mock_client = MagicMock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("网络错误")
            mock = MagicMock()
            mock.choices = [MagicMock()]
            mock.choices[0].message.content = "重试后成功。"
            return mock

        mock_client.chat.completions.create.side_effect = side_effect
        mock_openai_cls.return_value = mock_client

        interpreter_config.max_retries = 3
        interpreter = DeepSeekInterpreter(interpreter_config)
        summary = interpreter.generate_summary("前言内容。")

        assert call_count[0] == 2  # 1 次失败 + 1 次成功
        assert summary == "重试后成功。"


class TestInterpreterSection:
    """章节解读测试。"""

    @patch("bookwhisper.interpreter.OpenAI")
    def test_interpret_section(self, mock_openai_cls, interpreter_config, mock_openai_response, sample_section):
        """解读单个章节块。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        interpreter = DeepSeekInterpreter(interpreter_config)
        result = interpreter.interpret_section(sample_section, "整书摘要")

        assert result.original_chars == len(sample_section.text)
        assert result.interpreted_chars > 0
        assert result.interpreted_text == "这是解读后的文本内容。"

    @patch("bookwhisper.interpreter.OpenAI")
    def test_interpret_with_empty_summary(self, mock_openai_cls, interpreter_config, mock_openai_response, sample_section):
        """无整书摘要时也能正常解读。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        interpreter = DeepSeekInterpreter(interpreter_config)
        result = interpreter.interpret_section(sample_section, "")

        assert result.interpreted_chars > 0


class TestPreviousContext:
    """前文上下文传递测试。"""

    @patch("bookwhisper.interpreter.OpenAI")
    def test_previous_text_included_in_message(
        self, mock_openai_cls, interpreter_config, mock_openai_response, sample_section
    ):
        """传入 previous_text 时应出现在 user message 中。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        interpreter = DeepSeekInterpreter(interpreter_config)
        interpreter.interpret_section(
            sample_section, "整书摘要", previous_text="前一段的末尾内容..."
        )

        # 取出实际发送给 API 的 messages
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # 找到 user message
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert "【前文回顾】" in user_msg
        assert "前一段的末尾内容..." in user_msg

    @patch("bookwhisper.interpreter.OpenAI")
    def test_no_previous_text_when_empty(
        self, mock_openai_cls, interpreter_config, mock_openai_response, sample_section
    ):
        """不传 previous_text 时不应出现前文回顾标记。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        interpreter = DeepSeekInterpreter(interpreter_config)
        interpreter.interpret_section(sample_section, "整书摘要")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_msg = next(m["content"] for m in messages if m["role"] == "user")
        assert "【前文回顾】" not in user_msg


class TestRetryLogic:
    """重试逻辑测试。"""

    @patch("bookwhisper.interpreter.OpenAI")
    def test_retry_on_connection_error(self, mock_openai_cls, interpreter_config, sample_section):
        """连接错误应触发重试。"""
        mock_client = MagicMock()

        # 前 2 次失败，第 3 次成功
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("网络错误")
            mock = MagicMock()
            mock.choices = [MagicMock()]
            mock.choices[0].message.content = "重试后成功。"
            return mock

        mock_client.chat.completions.create.side_effect = side_effect
        mock_openai_cls.return_value = mock_client

        interpreter_config.max_retries = 3
        interpreter = DeepSeekInterpreter(interpreter_config)
        result = interpreter.interpret_section(sample_section, "摘要")

        # 应重试了 3 次（2 次失败 + 1 次成功）
        assert call_count[0] == 3
        assert result.interpreted_text == "重试后成功。"

    @patch("bookwhisper.interpreter.OpenAI")
    def test_retry_exhausted(self, mock_openai_cls, interpreter_config, sample_section):
        """重试耗尽后应抛出 InterpretError。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ConnectionError("持续网络错误")
        mock_openai_cls.return_value = mock_client

        interpreter_config.max_retries = 2
        interpreter = DeepSeekInterpreter(interpreter_config)
        with pytest.raises(InterpretError, match="已重试"):
            interpreter.interpret_section(sample_section, "摘要")

    @patch("bookwhisper.interpreter.OpenAI")
    def test_non_retryable_error(self, mock_openai_cls, interpreter_config, sample_section):
        """非可重试错误应直接抛出。"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ValueError("参数错误")
        mock_openai_cls.return_value = mock_client

        interpreter_config.max_retries = 3
        interpreter = DeepSeekInterpreter(interpreter_config)
        with pytest.raises(InterpretError):
            interpreter.interpret_section(sample_section, "摘要")
