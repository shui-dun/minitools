"""断点续传模块。

通过 JSON 文件记录每章的解读进度，支持中断后从断点恢复。
- 每次成功解读后立即 flush 到磁盘
- 用输入文件 SHA256 做 book_id，防止书籍混淆
- 区分网络错误（自动重试）和内容错误（不重试）
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# checkpoint 文件名
CHECKPOINT_FILENAME = ".bookwhisper_checkpoint.json"


@dataclass
class ChapterResult:
    """单章解读结果。"""

    chapter_id: str
    original_chars: int
    interpreted_chars: int
    interpreted_text: str = ""


class CheckpointManager:
    """管理解读进度的持久化。

    使用方式：
        cpm = CheckpointManager(output_dir, book_path)
        for chapter in chapters:
            if cpm.is_done(chapter.id):
                continue
            try:
                result = interpret(chapter)
                cpm.mark_done(chapter.id, result)
            except Exception as e:
                cpm.mark_failed(chapter.id, str(e))
                raise
    """

    def __init__(self, work_dir: Path, book_path: Path) -> None:
        """初始化 checkpoint 管理器。

        Args:
            work_dir: 输出目录，checkpoint 文件将存放在此。
            book_path: 输入书籍路径，用于计算 book_id。
        """
        self._work_dir = work_dir
        self._book_path = book_path
        self._checkpoint_path = work_dir / CHECKPOINT_FILENAME

        # 计算输入文件的 SHA256 作为 book_id
        self._book_id = self._compute_hash(book_path)

        # 加载或创建 checkpoint
        self._data: dict[str, Any] = self._load_or_create()

    # ---- 公共 API ----

    def is_done(self, chapter_id: str) -> bool:
        """该章节是否已成功解读？"""
        entry = self._data.get("completed_chapters", {}).get(chapter_id)
        return entry is not None and entry.get("status") == "done"

    def is_failed(self, chapter_id: str) -> bool:
        """该章节是否标记为失败？"""
        entry = self._data.get("completed_chapters", {}).get(chapter_id)
        return entry is not None and entry.get("status") == "failed"

    def mark_done(self, chapter_id: str, result: ChapterResult) -> None:
        """标记章节解读成功，立即写入文件。

        Args:
            chapter_id: 章节唯一标识。
            result: 解读结果。
        """
        completed = self._data.setdefault("completed_chapters", {})
        completed[chapter_id] = {
            "status": "done",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "original_chars": result.original_chars,
            "interpreted_chars": result.interpreted_chars,
            "api_calls": completed.get(chapter_id, {}).get("api_calls", 0) + 1,
        }
        self._flush()
        logger.info("第 %s 章解读完成 ✓", chapter_id)

    def mark_failed(self, chapter_id: str, error: str) -> None:
        """标记章节解读失败，记录重试次数。

        Args:
            chapter_id: 章节唯一标识。
            error: 错误描述。
        """
        completed = self._data.setdefault("completed_chapters", {})
        existing = completed.get(chapter_id, {})
        retry_count = existing.get("retry_count", 0) + 1
        completed[chapter_id] = {
            "status": "failed",
            "error": error,
            "retry_count": retry_count,
            "last_attempt": datetime.now(timezone.utc).isoformat(),
        }
        self._flush()
        logger.warning("第 %s 章解读失败（第 %d 次重试）: %s", chapter_id, retry_count, error)

    def get_pending(self) -> list[str]:
        """获取尚未完成的章节 ID 列表（包括需要重试的 failed 章节）。"""
        completed = self._data.get("completed_chapters", {})
        all_ids: set[str] = set()
        for ch_id, entry in completed.items():
            if entry.get("status") != "done":
                all_ids.add(ch_id)
        return sorted(all_ids)

    def get_failed_ids(self) -> list[str]:
        """获取标记为 failed 的章节 ID 列表。"""
        completed = self._data.get("completed_chapters", {})
        return sorted(
            ch_id for ch_id, entry in completed.items()
            if entry.get("status") == "failed"
        )

    def set_book_summary(self, summary: str) -> None:
        """保存整书摘要（避免中断后重新生成）。"""
        self._data["book_summary"] = summary
        self._flush()

    def get_book_summary(self) -> str | None:
        """获取已保存的整书摘要，若不存在返回 None。"""
        return self._data.get("book_summary")

    def set_total_chapters(self, total: int) -> None:
        """设置总章节数。"""
        self._data["total_chapters"] = total
        self._flush()

    @property
    def progress(self) -> tuple[int, int]:
        """返回 (已完成数, 总章节数)。"""
        completed = self._data.get("completed_chapters", {})
        total = self._data.get("total_chapters", 0)
        done = sum(1 for entry in completed.values() if entry.get("status") == "done")
        return done, total

    @property
    def all_done(self) -> bool:
        """是否所有章节都已解读完成？"""
        done, total = self.progress
        return total > 0 and done >= total

    def reset_chapter(self, chapter_id: str) -> None:
        """重置单个章节的状态（用于手动重试）。"""
        completed = self._data.get("completed_chapters", {})
        if chapter_id in completed:
            del completed[chapter_id]
            self._flush()

    # ---- 内部方法 ----

    def _load_or_create(self) -> dict[str, Any]:
        """加载已有 checkpoint，或创建新的。"""
        if self._checkpoint_path.exists():
            try:
                raw = self._checkpoint_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                # 校验 book_id：如果输入文件变了，自动创建新 checkpoint
                if data.get("book_id") != self._book_id:
                    logger.info(
                        "检测到输入文件已变更（book_id 不匹配），创建新 checkpoint"
                    )
                    return self._create_new()
                logger.info(
                    "加载已有 checkpoint: %d/%d 章已完成",
                    sum(1 for e in data.get("completed_chapters", {}).values() if e.get("status") == "done"),
                    data.get("total_chapters", 0),
                )
                return data
            except (json.JSONDecodeError, KeyError):
                logger.warning("Checkpoint 文件损坏，创建新 checkpoint")
                return self._create_new()
        else:
            return self._create_new()

    def _create_new(self) -> dict[str, Any]:
        """创建新的 checkpoint 数据结构。"""
        work_dir = self._work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "book_id": self._book_id,
            "book_title": self._book_path.stem,
            "input_hash": self._book_id,
            "total_chapters": 0,
            "completed_chapters": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._checkpoint_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data

    def _flush(self) -> None:
        """立即将数据写入磁盘。"""
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._checkpoint_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        """计算文件的 SHA256 哈希。"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]  # 取前 16 位足够区分
