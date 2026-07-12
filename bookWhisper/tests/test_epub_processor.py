"""epub_processor.py 单元测试。"""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from bookwhisper.epub_processor import EpubReader, EpubWriter


class TestEpubReader:
    """EPUB 读取测试。"""

    def test_load_chapters(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        chapters = reader.chapters
        # 应有 2 章
        assert len(chapters) == 2

    def test_chapter_order(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        chapters = reader.chapters
        assert chapters[0].index == 0
        assert chapters[1].index == 1

    def test_chapter_has_content(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        for ch in reader.chapters:
            assert len(ch.plain_text) > 0
            assert ch.char_count > 0

    def test_title_detection(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        chapters = reader.chapters
        # 第 1 章标题应包含"引言"或"第一章"
        assert "引言" in chapters[0].title or "第一章" in chapters[0].title
        # 第 2 章标题应包含"深度分析"或"第二章"
        assert "深度分析" in chapters[1].title or "第二章" in chapters[1].title

    def test_book_title(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        assert reader.title == "测试书籍"

    def test_total_chars(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        assert reader.total_chars > 0

    def test_get_chapter(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        ch0 = reader.get_chapter(0)
        assert ch0 is not None
        assert ch0.index == 0

        # 超出范围
        assert reader.get_chapter(999) is None

    def test_get_front_matter(self, sample_epub_path: Path) -> None:
        reader = EpubReader(sample_epub_path)
        front = reader.get_front_matter_text(max_chars=500)
        assert len(front) > 0
        assert len(front) <= 500


class TestEpubWriter:
    """EPUB 写入测试。"""

    def test_write_and_reread(self, sample_epub_path: Path, tmp_path: Path) -> None:
        """写入新 EPUB 后能正常重新读取。"""
        reader = EpubReader(sample_epub_path)
        writer = EpubWriter(reader.book)

        # 准备解读结果
        chapter_results = {
            0: "这是第一章的解读内容。\n\n口语化的表达。",
            1: "这是第二章的深度分析解读。\n\n更加通俗易懂。",
        }

        output_path = tmp_path / "output.epub"
        result = writer.write(output_path, chapter_results)

        assert result.exists()
        assert result.suffix == ".epub"

        # 重新读取验证
        reader2 = EpubReader(result)
        assert len(reader2.chapters) > 0

    def test_preserve_metadata(self, sample_epub_path: Path, tmp_path: Path) -> None:
        """输出 EPUB 应保留原书的元数据。"""
        reader = EpubReader(sample_epub_path)
        original_title = reader.title

        writer = EpubWriter(reader.book)
        chapter_results = {0: "测试内容。", 1: "测试内容。"}
        output_path = tmp_path / "output.epub"
        writer.write(output_path, chapter_results)

        reader2 = EpubReader(output_path)
        # 书名应包含原标题（可能加了后缀）
        assert original_title in reader2.title or "测试" in reader2.title

    def test_empty_chapters(self, sample_epub_path: Path, tmp_path: Path) -> None:
        """空 chapter_results 不应崩溃。"""
        reader = EpubReader(sample_epub_path)
        writer = EpubWriter(reader.book)

        output_path = tmp_path / "empty_output.epub"
        result = writer.write(output_path, {})
        assert result.exists()
