"""checkpoint.py 单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwhisper.checkpoint import ChapterResult, CheckpointManager, CHECKPOINT_FILENAME


class TestCheckpointManager:
    """断点续传单元测试。"""

    def test_new_checkpoint(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """首次运行应创建新 checkpoint。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        checkpoint_file = tmp_path / CHECKPOINT_FILENAME
        assert checkpoint_file.exists()

    def test_is_done_false_initially(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """新建 checkpoint 时所有章节应为未完成。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        assert not cpm.is_done("chapter_000")
        assert not cpm.is_done("chapter_001")

    def test_mark_done(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """标记完成后 is_done 应返回 True。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)

        result = ChapterResult(
            chapter_id="chapter_000",
            original_chars=100,
            interpreted_chars=80,
        )
        cpm.mark_done("chapter_000", result)

        assert cpm.is_done("chapter_000")
        assert not cpm.is_done("chapter_001")

    def test_mark_failed(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """标记失败后 get_pending 应包含该章节。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)

        cpm.mark_failed("chapter_000", "ConnectionError")

        pending = cpm.get_pending()
        assert "chapter_000" in pending

    def test_resume_from_checkpoint(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """从已有 checkpoint 恢复。"""
        # 先创建并标记完成
        cpm1 = CheckpointManager(tmp_path, sample_epub_path)
        cpm1.mark_done("chapter_000", ChapterResult("chapter_000", 100, 80))

        # 重新加载
        cpm2 = CheckpointManager(tmp_path, sample_epub_path)
        assert cpm2.is_done("chapter_000")

    def test_progress_tracking(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """progress 属性正确跟踪进度。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        cpm.set_total_chapters(10)

        assert cpm.progress == (0, 10)

        cpm.mark_done("chapter_000", ChapterResult("chapter_000", 100, 80))
        cpm.mark_done("chapter_001", ChapterResult("chapter_001", 200, 150))
        cpm.mark_failed("chapter_002", "Timeout")

        done, total = cpm.progress
        assert done == 2
        assert total == 10

    def test_all_done(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """all_done 在所有章节完成后返回 True。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        cpm.set_total_chapters(2)
        cpm.mark_done("chapter_000", ChapterResult("chapter_000", 100, 80))
        cpm.mark_done("chapter_001", ChapterResult("chapter_001", 200, 150))

        assert cpm.all_done

    def test_different_book_new_checkpoint(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """不同书籍应创建不同 checkpoint（book_id 不匹配）。"""
        cpm1 = CheckpointManager(tmp_path, sample_epub_path)
        cpm1.mark_done("chapter_000", ChapterResult("chapter_000", 100, 80))

        # 用不同的文件
        other_book = tmp_path / "other.epub"
        other_book.write_text("different content")

        cpm2 = CheckpointManager(tmp_path, other_book)
        assert not cpm2.is_done("chapter_000")

    def test_book_summary_persistence(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """整书摘要应正确持久化。"""
        cpm1 = CheckpointManager(tmp_path, sample_epub_path)
        summary = "这是一份测试摘要。"
        cpm1.set_book_summary(summary)

        cpm2 = CheckpointManager(tmp_path, sample_epub_path)
        assert cpm2.get_book_summary() == summary

    def test_corrupted_checkpoint(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """损坏的 checkpoint 不应崩溃，应重建新文件。"""
        checkpoint_file = tmp_path / CHECKPOINT_FILENAME
        checkpoint_file.write_text("this is not valid json", encoding="utf-8")

        # 不应崩溃
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        assert not cpm.is_done("chapter_000")

    def test_reset_chapter(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """reset_chapter 应清除章节状态。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        cpm.mark_done("chapter_000", ChapterResult("chapter_000", 100, 80))
        assert cpm.is_done("chapter_000")

        cpm.reset_chapter("chapter_000")
        assert not cpm.is_done("chapter_000")

    def test_get_failed_ids(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """get_failed_ids 应返回所有失败章节。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)

        cpm.mark_failed("chapter_000", "Timeout")
        cpm.mark_failed("chapter_002", "ConnectionError")
        cpm.mark_done("chapter_001", ChapterResult("chapter_001", 100, 80))

        failed = cpm.get_failed_ids()
        assert "chapter_000" in failed
        assert "chapter_002" in failed
        assert "chapter_001" not in failed
