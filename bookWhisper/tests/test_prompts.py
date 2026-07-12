"""prompts.py 单元测试。"""

from __future__ import annotations

from bookwhisper.prompts import SUMMARY_PROMPT, SYSTEM_PROMPT


class TestPrompts:
    """提示词模板测试。"""

    def test_system_prompt_not_empty(self) -> None:
        """System prompt 不为空。"""
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_key_requirements(self) -> None:
        """System prompt 包含所有 8 条核心要求。"""
        assert "去啰嗦" in SYSTEM_PROMPT
        assert "去晦涩" in SYSTEM_PROMPT
        assert "口语化" in SYSTEM_PROMPT
        assert "翻译腔" in SYSTEM_PROMPT
        assert "括号融合" in SYSTEM_PROMPT
        assert "术语首次出现时" in SYSTEM_PROMPT
        assert "术语停顿" in SYSTEM_PROMPT or "断句" in SYSTEM_PROMPT
        assert "有趣" in SYSTEM_PROMPT

    def test_summary_prompt_format(self) -> None:
        """摘要 prompt 支持 format 变量。"""
        formatted = SUMMARY_PROMPT.format(max_chars=500, content="测试内容")
        assert "500" in formatted
        assert "测试内容" in formatted
