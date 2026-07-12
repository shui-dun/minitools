"""文本分章模块。

从 EPUB 提取的章节列表中，将超长章节按段落边界进一步切分，
确保每个块不超过 max_chars 限制。
"""

from __future__ import annotations

import logging

from bookwhisper.epub_processor import Chapter, Section

logger = logging.getLogger(__name__)


class ChapterSplitter:
    """将章节切分为适合 LLM 处理的块。

    策略：
    - 短于 max_chars 的章节 → 整章作为一块
    - 超出 max_chars 的章节 → 按段落边界（双换行）切分，
      每块 ≤ max_chars，不做块间重叠。

    用法：
        splitter = ChapterSplitter(max_chars=3000)
        sections = splitter.split_chapters(reader.chapters)
    """

    def __init__(self, max_chars: int = 3000) -> None:
        """初始化。

        Args:
            max_chars: 单块最大字符数。
        """
        if max_chars < 100:
            raise ValueError(f"max_chars 过小（{max_chars}），最小值为 100")
        self._max_chars = max_chars

    def split_chapters(self, chapters: list[Chapter]) -> list[Section]:
        """将章节列表切分为处理块。

        Args:
            chapters: Chapter 对象列表。

        Returns:
            Section 对象列表。
        """
        sections: list[Section] = []
        for chapter in chapters:
            chapter_sections = self.split_one(chapter)
            sections.extend(chapter_sections)

        logger.info(
            "分块完成: %d 个章节 → %d 个处理块 (max_chars=%d)",
            len(chapters),
            len(sections),
            self._max_chars,
        )
        return sections

    def split_one(self, chapter: Chapter) -> list[Section]:
        """将单个章节切分为若干块。

        Args:
            chapter: Chapter 对象。

        Returns:
            Section 对象列表。
        """
        text = chapter.plain_text

        # 空章节
        if not text.strip():
            return []

        # 短于 max_chars → 整章作为一块
        if len(text) <= self._max_chars:
            return [
                Section(
                    chapter_index=chapter.index,
                    chapter_title=chapter.title,
                    section_index=0,
                    total_sections=1,
                    text=text,
                )
            ]

        # 长章节 → 按段落边界切分
        paragraphs = self._split_paragraphs(text)
        return self._build_sections(chapter, paragraphs)

    def _split_paragraphs(self, text: str) -> list[str]:
        """按双换行（段落边界）切分文本。"""
        raw = text.split("\n\n")
        # 过滤空段落，但保留单换行
        result: list[str] = []
        for para in raw:
            stripped = para.strip()
            if stripped:
                result.append(stripped)
        return result

    def _build_sections(
        self, chapter: Chapter, paragraphs: list[str]
    ) -> list[Section]:
        """将段落列表组装为不超过 max_chars 的 Section 块。

        采用贪心策略：尽可能多地将段落放入当前块，直到超出限制。
        如果单个段落超出限制，则按句子边界二次切分。
        """
        chunks: list[list[str]] = []
        current_chunk: list[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)

            # 单个段落就超出限制：按句子切分
            if para_len > self._max_chars:
                # 先保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_len = 0

                sub_chunks = self._split_long_paragraph(para)
                chunks.extend(sub_chunks)
                continue

            # 加入当前块会超出限制 → 开始新块
            if current_len + para_len + 2 > self._max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [para]
                current_len = para_len
            else:
                current_chunk.append(para)
                current_len += para_len + 2  # +2 为段落间分隔符

        # 不要遗漏最后一块
        if current_chunk:
            chunks.append(current_chunk)

        # 组装为 Section 对象
        total = len(chunks)
        sections: list[Section] = []
        for i, chunk_paras in enumerate(chunks):
            sections.append(Section(
                chapter_index=chapter.index,
                chapter_title=chapter.title,
                section_index=i,
                total_sections=total,
                text="\n\n".join(chunk_paras),
            ))

        return sections

    def _split_long_paragraph(self, paragraph: str) -> list[list[str]]:
        """将超长段落按句子边界切分为多个子块。

        中文句子分隔符：。！？
        """
        # 按句子分隔符切分
        sentences: list[str] = []
        current = ""
        for char in paragraph:
            current += char
            if char in "。！？\n":
                sentences.append(current)
                current = ""
        if current.strip():
            sentences.append(current)

        # 贪心组装
        chunks: list[list[str]] = []
        current_chunk: list[str] = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > self._max_chars and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [sent]
                current_len = sent_len
            else:
                current_chunk.append(sent)
                current_len += sent_len

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
