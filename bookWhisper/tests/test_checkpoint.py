"""checkpoint.py 单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwhisper.checkpoint import ChapterResult, CheckpointManager, checkpoint_path_for


class TestCheckpointManager:
    """断点续传单元测试。"""

    def test_new_checkpoint(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """首次运行应创建新 checkpoint。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        checkpoint_file = checkpoint_path_for(tmp_path, sample_epub_path)
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
        checkpoint_file = checkpoint_path_for(tmp_path, sample_epub_path)
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

    def test_interpreted_text_persisted(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """解读文本应随 mark_done 持久化，并通过 get_result 恢复。"""
        cpm1 = CheckpointManager(tmp_path, sample_epub_path)
        sample_text = "这是 AI 解读后的章节文本，包含口语化转写内容。"
        cpm1.mark_done(
            "chapter_000",
            ChapterResult(
                chapter_id="chapter_000",
                original_chars=100,
                interpreted_chars=50,
                interpreted_text=sample_text,
            ),
        )

        # 重新加载 checkpoint
        cpm2 = CheckpointManager(tmp_path, sample_epub_path)
        result = cpm2.get_result("chapter_000")

        assert result is not None
        assert result.interpreted_text == sample_text
        assert result.original_chars == 100
        assert result.interpreted_chars == 50
        assert result.chapter_id == "chapter_000"

    def test_get_all_results(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """get_all_results 应返回所有已完成章节的完整文本。"""
        cpm = CheckpointManager(tmp_path, sample_epub_path)
        cpm.set_total_chapters(3)

        cpm.mark_done("chapter_000", ChapterResult("chapter_000", 100, 80, "文本零"))
        cpm.mark_done("chapter_001", ChapterResult("chapter_001", 200, 150, "文本一"))
        cpm.mark_failed("chapter_002", "Timeout")  # 失败的不会被返回

        all_results = cpm.get_all_results()
        assert len(all_results) == 2
        assert "chapter_000" in all_results
        assert "chapter_001" in all_results
        assert "chapter_002" not in all_results  # 失败的不算完成
        assert all_results["chapter_000"].interpreted_text == "文本零"
        assert all_results["chapter_001"].interpreted_text == "文本一"

    def test_old_checkpoint_without_text(self, tmp_path: Path, sample_epub_path: Path) -> None:
        """旧版 checkpoint（没有 interpreted_text 字段）应返回 None，不会崩溃。"""
        import json

        # 手动构造旧版格式的 checkpoint
        old_data = {
            "book_id": CheckpointManager._compute_hash(sample_epub_path),
            "book_title": "test",
            "input_hash": CheckpointManager._compute_hash(sample_epub_path),
            "total_chapters": 1,
            "completed_chapters": {
                "chapter_000": {
                    "status": "done",
                    "completed_at": "2026-01-01T00:00:00+00:00",
                    "original_chars": 100,
                    "interpreted_chars": 80,
                    "api_calls": 1,
                    # 注意：没有 interpreted_text 字段（旧版格式）
                }
            },
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        checkpoint_file = checkpoint_path_for(tmp_path, sample_epub_path)
        checkpoint_file.write_text(json.dumps(old_data, ensure_ascii=False), encoding="utf-8")

        cpm = CheckpointManager(tmp_path, sample_epub_path)
        # is_done 仍然返回 True（状态是完成的）
        assert cpm.is_done("chapter_000")
        # 但 get_result 返回 None（因为没有文本）
        assert cpm.get_result("chapter_000") is None
        # get_all_results 也不会包含这个章节
        assert len(cpm.get_all_results()) == 0
