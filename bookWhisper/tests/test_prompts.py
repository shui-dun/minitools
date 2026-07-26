"""prompts.py 单元测试。"""

from __future__ import annotations

from bookwhisper.prompts import REVIEW_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT


class TestPrompts:
    """提示词模板测试。"""

    def test_system_prompt_not_empty(self) -> None:
        """System prompt 不为空。"""
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_key_requirements(self) -> None:
        """System prompt 包含所有核心要求。"""
        assert "口语化" in SYSTEM_PROMPT
        assert "有趣" in SYSTEM_PROMPT
        assert "不常用" in SYSTEM_PROMPT
        assert "通俗" in SYSTEM_PROMPT
        assert "不要使用括号" in SYSTEM_PROMPT
        assert "首次出现时" in SYSTEM_PROMPT
        assert "不要使用长度为1的词语" in SYSTEM_PROMPT
        assert "解说员" in SYSTEM_PROMPT

    def test_summary_prompt_format(self) -> None:
        """摘要 prompt 支持 format 变量。"""
        formatted = SUMMARY_PROMPT.format(max_chars=500, content="测试内容")
        assert "500" in formatted
        assert "测试内容" in formatted

    def test_review_prompt_not_empty(self) -> None:
        """审核重写 prompt 不为空。"""
        assert len(REVIEW_PROMPT) > 50

    def test_review_prompt_format(self) -> None:
        """审核重写 prompt 支持 format 变量。"""
        formatted = REVIEW_PROMPT.format(content="测试通俗化结果")
        assert "测试通俗化结果" in formatted
        assert "全文重写" in formatted
