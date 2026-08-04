"""prompts.py 单元测试。"""

from __future__ import annotations

from bookwhisper.prompts import (
    NOVEL_SYSTEM_PROMPT,
    REVIEW_PROMPT,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)


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


class TestNovelPrompt:
    """novel 模式提示词测试。"""

    def test_novel_prompt_not_empty(self) -> None:
        """NOVEL prompt 不为空。"""
        assert len(NOVEL_SYSTEM_PROMPT) > 100

    def test_novel_prompt_minimal_changes(self) -> None:
        """NOVEL prompt 强调尽量保持原文。"""
        assert "尽量保持原文" in NOVEL_SYSTEM_PROMPT
        assert "不是重写" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_ocr_fix(self) -> None:
        """NOVEL prompt 包含 OCR 修正要求。"""
        assert "OCR" in NOVEL_SYSTEM_PROMPT
        assert "错别字" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_replace_uncommon_words(self) -> None:
        """NOVEL prompt 包含不常用词替换要求。"""
        assert "不常用" in NOVEL_SYSTEM_PROMPT
        assert "吊诡" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_single_char_words(self) -> None:
        """NOVEL prompt 包含单字词替换要求。"""
        assert "单个字的词语" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_dialogue_reorder(self) -> None:
        """NOVEL prompt 包含对话顺序改写要求。"""
        assert "他说道" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_classical_to_vernacular(self) -> None:
        """NOVEL prompt 包含文言文改写要求。"""
        assert "文言文" in NOVEL_SYSTEM_PROMPT
        assert "白话文" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_text_alignment(self) -> None:
        """NOVEL prompt 包含文本对齐要求。"""
        assert "对齐" in NOVEL_SYSTEM_PROMPT
        assert "不完整" in NOVEL_SYSTEM_PROMPT

    def test_novel_prompt_no_meta_output(self) -> None:
        """NOVEL prompt 要求直接输出正文，不要额外说明。"""
        assert "直接输出优化后的正文" in NOVEL_SYSTEM_PROMPT
        assert "不要添加任何说明" in NOVEL_SYSTEM_PROMPT
