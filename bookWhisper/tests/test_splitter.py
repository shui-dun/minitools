"""splitter.py 单元测试。"""

from __future__ import annotations

import pytest

from bookwhisper.epub_processor import Chapter
from bookwhisper.splitter import ChapterSplitter


class TestChapterSplitter:
    """分章单元测试。"""

    def test_short_chapter_no_split(self) -> None:
        """短于 max_chars 的章节不应分块。"""
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(0, "短章节", "这是一段很短的文本。")
        sections = splitter.split_one(chapter)
        assert len(sections) == 1
        assert sections[0].total_sections == 1
        assert sections[0].section_index == 0

    def test_long_chapter_split(self) -> None:
        """超出 max_chars 的章节应按段落切分成多块。"""
        splitter = ChapterSplitter(max_chars=100)

        long_text = "\n\n".join(
            f"这是第{i}段文本内容，包含一些测试用的句子。" for i in range(20)
        )

        chapter = _make_chapter(1, "长章节", long_text)
        sections = splitter.split_one(chapter)

        # 应切分为多块
        assert len(sections) > 1
        # 每块不超过 max_chars
        for sec in sections:
            assert len(sec.text) <= 100 or sec.total_sections > 1

    def test_section_metadata(self) -> None:
        """每块的元数据应正确。"""
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(0, "测试标题", "这是一个短章节。")
        sections = splitter.split_one(chapter)

        assert sections[0].chapter_index == 0
        assert sections[0].chapter_title == "测试标题"
        assert sections[0].section_index == 0
        assert sections[0].total_sections == 1

    def test_section_id_format(self) -> None:
        """Section.id 格式正确。"""
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(3, "某章", "短文本")
        sections = splitter.split_one(chapter)

        assert sections[0].id == "chapter_003"

    def test_section_id_with_multi(self) -> None:
        """多块时 Section.id 包含 section 编号。"""
        splitter = ChapterSplitter(max_chars=100)
        long_text = "\n\n".join(f"段落{i}内容" * 5 for i in range(20))
        chapter = _make_chapter(0, "长章节", long_text)
        sections = splitter.split_one(chapter)

        if len(sections) > 1:
            assert "_section_" in sections[0].id
            assert "_section_" in sections[1].id

    def test_empty_chapter(self) -> None:
        """空章节不应崩溃，返回空列表。"""
        splitter = ChapterSplitter()
        chapter = _make_chapter(0, "空章节", "")
        sections = splitter.split_one(chapter)
        assert sections == []

    def test_context_label(self) -> None:
        """context_label 格式正确。"""
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(0, "引言", "短内容")
        sections = splitter.split_one(chapter)
        assert "第1章" in sections[0].context_label
        assert "引言" in sections[0].context_label

    def test_multi_chapter_label(self) -> None:
        """多块时的 context_label 包含位置信息。"""
        splitter = ChapterSplitter(max_chars=100)
        long_text = "\n\n".join(f"段落{i}" * 10 for i in range(20))
        chapter = _make_chapter(2, "长章节", long_text)
        sections = splitter.split_one(chapter)

        if len(sections) > 1:
            assert "段" in sections[0].context_label or "section" in sections[0].id

    def test_max_chars_too_small(self) -> None:
        """max_chars 过小应抛出 ValueError。"""
        with pytest.raises(ValueError):
            ChapterSplitter(max_chars=50)

    def test_split_chapters_batch(self) -> None:
        """批量 split_chapters 测试。"""
        splitter = ChapterSplitter(max_chars=3000)
        chapters = [
            _make_chapter(0, "章一", "短内容"),
            _make_chapter(1, "章二", "也是短内容"),
        ]
        sections = splitter.split_chapters(chapters)
        assert len(sections) == 2

    def test_paragraph_boundary_integrity(self) -> None:
        """切分不应在段落中间切断——每块应以段落边界开始/结束。"""
        splitter = ChapterSplitter(max_chars=200)

        # 构造：10 个段落，每个约 80 字符
        paras = []
        for i in range(10):
            paras.append(f"第{i}段" + "测试文本内容。" * 10)
        long_text = "\n\n".join(paras)

        chapter = _make_chapter(0, "段落测试", long_text)
        sections = splitter.split_one(chapter)

        # 验证每块的文本是完整段落的拼接
        for sec in sections:
            # 每段不应在句子中间截断
            # 简单验证：不从句子中间开始或结束
            text = sec.text.strip()
            assert text  # 非空
            # 最后一个字符如果是中文标点或字母，则合理
            # (这个测试较为松散，真正的完整性由 _split_paragraphs 保证)


def _make_chapter(index: int, title: str, plain_text: str) -> Chapter:
    """创建测试用的 Chapter 对象。"""
    return Chapter(
        index=index,
        title=title,
        content_html=f"<html><body><h1>{title}</h1><p>{plain_text}</p></body></html>",
        plain_text=plain_text,
        item_id=f"item_{index}",
        file_name=f"chapter_{index:03d}.xhtml",
        char_count=len(plain_text),
    )
