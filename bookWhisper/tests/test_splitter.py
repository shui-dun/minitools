"""splitter.py 单元测试。

使用真实 EPUB 章节验证分块行为，合成章节用于边界条件测试。
"""

from __future__ import annotations

import pytest

from bookwhisper.epub_processor import Chapter, EpubReader
from bookwhisper.splitter import ChapterSplitter, Section


# ==================== 真实书籍测试 ====================


class TestSplitterRealBook:
    """使用真实 EPUB（金枝）验证 ChapterSplitter。"""

    def test_split_real_book(self, real_reader: EpubReader) -> None:
        """真实书籍 73 章应能正常分块，不崩溃。"""
        splitter = ChapterSplitter(max_chars=3000)
        sections = splitter.split_chapters(real_reader.chapters)

        # 73 章 → 至少 73 个 section
        assert len(sections) >= 73, f"应至少有 73 个 section，实际 {len(sections)}"

        # 总字符数守恒（允许少量差异，因空段落过滤）
        total_chars_in = sum(len(sec.text) for sec in sections)
        total_chars_book = real_reader.total_chars
        # 字符数差异应在 10% 以内（空段落过滤、空白规范化等会导致微小差异）
        diff_ratio = abs(total_chars_in - total_chars_book) / max(total_chars_book, 1)
        assert diff_ratio < 0.10, \
            f"分块后总字符数 ({total_chars_in}) 与原著 ({total_chars_book}) 差异过大 ({diff_ratio:.2%})"

    def test_each_section_under_max_chars(self, real_reader: EpubReader) -> None:
        """每块文本不应超过 max_chars（多块章节除外）。"""
        splitter = ChapterSplitter(max_chars=3000)
        sections = splitter.split_chapters(real_reader.chapters)

        for sec in sections:
            assert len(sec.text) <= 3000, \
                f"Section {sec.id} 超出限制: {len(sec.text)} > 3000"

    def test_section_context_label(self, real_reader: EpubReader) -> None:
        """每个 section 的 context_label 应包含章节信息。"""
        splitter = ChapterSplitter(max_chars=3000)
        sections = splitter.split_chapters(real_reader.chapters)

        for sec in sections:
            assert "章" in sec.context_label, \
                f"context_label 应包含 '章': {sec.context_label}"
            assert sec.chapter_title in sec.context_label, \
                f"context_label 应包含章节标题: {sec.context_label}"

    def test_long_chapter_gets_split(self, real_reader: EpubReader) -> None:
        """真实书籍中长章节应被切分成多块，且每块不超过 max_chars。"""
        # 找到第一个远超 max_chars 的章节
        long_ch = None
        for ch in real_reader.chapters:
            if ch.char_count > 10000:
                long_ch = ch
                break

        assert long_ch is not None, "应存在超过 10000 字符的长章节用于测试"
        assert long_ch.char_count > 3000

        splitter = ChapterSplitter(max_chars=3000)
        sections = splitter.split_one(long_ch)

        assert len(sections) > 1, \
            f"章节 '{long_ch.title}' ({long_ch.char_count} 字符) 应被切分成多块"

        # 每块不能超过限制（包括代码修复后的强制截断）
        for sec in sections:
            assert len(sec.text) <= 3000, \
                f"Section {sec.id} 长度 {len(sec.text)} 超过 max_chars=3000"

        # 多块时 section id 应包含 "_section_"
        for sec in sections:
            assert "_section_" in sec.id, \
                f"多块章节的 section id 应包含 _section_: {sec.id}"

    def test_short_chapter_not_split(self, real_reader: EpubReader) -> None:
        """短章节（如第一章引言 146 字符）不应被切分。"""
        short_ch = real_reader.get_chapter(1)  # 第 2 章，约 146 字符
        assert short_ch is not None
        assert short_ch.char_count < 3000, \
            f"测试前提：章节应短于 max_chars ({short_ch.char_count})"

        splitter = ChapterSplitter(max_chars=3000)
        sections = splitter.split_one(short_ch)

        assert len(sections) == 1
        assert sections[0].total_sections == 1
        assert sections[0].section_index == 0


# ==================== 合成数据边界测试 ====================


class TestChapterSplitter:
    """边界条件和合成数据测试。"""

    def test_short_chapter_no_split(self) -> None:
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(0, "短章节", "这是一段很短的文本。")
        sections = splitter.split_one(chapter)
        assert len(sections) == 1
        assert sections[0].total_sections == 1

    def test_long_chapter_split(self) -> None:
        """超出 max_chars 的章节应按段落切分成多块。"""
        splitter = ChapterSplitter(max_chars=100)

        long_text = "\n\n".join(
            f"这是第{i}段文本内容，包含一些测试用的句子。" for i in range(20)
        )
        chapter = _make_chapter(1, "长章节", long_text)
        sections = splitter.split_one(chapter)

        assert len(sections) > 1
        for sec in sections:
            assert len(sec.text) <= 100

    def test_section_metadata(self) -> None:
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(0, "测试标题", "这是一个短章节。")
        sections = splitter.split_one(chapter)

        assert sections[0].chapter_index == 0
        assert sections[0].chapter_title == "测试标题"
        assert sections[0].section_index == 0
        assert sections[0].total_sections == 1

    def test_section_id_format(self) -> None:
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(3, "某章", "短文本")
        sections = splitter.split_one(chapter)
        assert sections[0].id == "chapter_003"

    def test_section_id_with_multi(self) -> None:
        splitter = ChapterSplitter(max_chars=100)
        long_text = "\n\n".join(f"段落{i}内容" * 5 for i in range(20))
        chapter = _make_chapter(0, "长章节", long_text)
        sections = splitter.split_one(chapter)

        if len(sections) > 1:
            assert "_section_" in sections[0].id
            assert "_section_" in sections[1].id

    def test_empty_chapter(self) -> None:
        splitter = ChapterSplitter()
        chapter = _make_chapter(0, "空章节", "")
        sections = splitter.split_one(chapter)
        assert sections == []

    def test_whitespace_only_chapter(self) -> None:
        """纯空白的章节应返回空列表。"""
        splitter = ChapterSplitter()
        chapter = _make_chapter(0, "空白", "\n\n   \n")
        sections = splitter.split_one(chapter)
        assert sections == []

    def test_context_label(self) -> None:
        splitter = ChapterSplitter(max_chars=3000)
        chapter = _make_chapter(0, "引言", "短内容")
        sections = splitter.split_one(chapter)
        assert "第1章" in sections[0].context_label
        assert "引言" in sections[0].context_label

    def test_multi_chapter_label(self) -> None:
        splitter = ChapterSplitter(max_chars=100)
        long_text = "\n\n".join(f"段落{i}" * 10 for i in range(20))
        chapter = _make_chapter(2, "长章节", long_text)
        sections = splitter.split_one(chapter)

        if len(sections) > 1:
            assert "段" in sections[0].context_label or "section" in sections[0].id

    def test_max_chars_too_small(self) -> None:
        with pytest.raises(ValueError):
            ChapterSplitter(max_chars=50)

    def test_split_chapters_batch(self) -> None:
        splitter = ChapterSplitter(max_chars=3000)
        chapters = [
            _make_chapter(0, "章一", "短内容"),
            _make_chapter(1, "章二", "也是短内容"),
        ]
        sections = splitter.split_chapters(chapters)
        assert len(sections) == 2

    def test_paragraph_boundary_integrity(self) -> None:
        """切分应在段落边界处进行，不应从段落中间截断。

        验证方法：每块的文本应可拆回完整的段落（无截断痕迹），
        且所有块的段落拼接应等于原文章的段落。
        """
        splitter = ChapterSplitter(max_chars=200)

        # 构造：10 个段落，每个约 80 字符
        paras = []
        for i in range(10):
            paras.append(f"第{i}段" + "测试文本内容。" * 10)
        long_text = "\n\n".join(paras)

        chapter = _make_chapter(0, "段落测试", long_text)
        sections = splitter.split_one(chapter)

        # 将所有 section 中的段落全部提取出来，拼接起来
        all_section_paras: list[str] = []
        for sec in sections:
            sec_paras = sec.text.split("\n\n")
            all_section_paras.extend(p.strip() for p in sec_paras if p.strip())

        # 与原始段落一一对应
        original_paras = [p.strip() for p in paras if p.strip()]
        assert len(all_section_paras) == len(original_paras), \
            f"段落数不匹配: {len(all_section_paras)} vs {len(original_paras)}"

        for i, (orig, rebuilt) in enumerate(zip(original_paras, all_section_paras)):
            assert orig == rebuilt, \
                f"段落 {i} 不匹配:\n  原始: {orig[:60]}...\n  重建: {rebuilt[:60]}..."

    def test_section_continuity(self) -> None:
        """多块章节的 section_index 应连续且 total_sections 一致。"""
        splitter = ChapterSplitter(max_chars=100)
        long_text = "\n\n".join(f"段落{i}内容" * 5 for i in range(20))
        chapter = _make_chapter(0, "连续性测试", long_text)
        sections = splitter.split_one(chapter)

        if len(sections) > 1:
            total = sections[0].total_sections
            assert total == len(sections), \
                f"total_sections ({total}) 应等于实际块数 ({len(sections)})"

            for i, sec in enumerate(sections):
                assert sec.section_index == i, \
                    f"section_index 应连续: 期望 {i}, 实际 {sec.section_index}"
                assert sec.total_sections == total, \
                    f"total_sections 应一致: 期望 {total}, 实际 {sec.total_sections}"


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
