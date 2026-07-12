"""EPUB 处理模块。

基于 ebooklib + BeautifulSoup 实现：
- EpubReader：读取 EPUB，提取章节结构和正文文本
- EpubWriter：用解读后的文本替换原章节内容，保留插图/CSS/元数据/ToC
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

import ebooklib
from ebooklib import epub

logger = logging.getLogger(__name__)


# ---- 数据类 ----

@dataclass
class Chapter:
    """书籍中的一个章节。"""

    index: int            # 章节序号（从 0 开始）
    title: str            # 章节标题
    content_html: str     # 原始 HTML 内容
    plain_text: str       # 提取的纯文本（用于发送给 LLM）
    item_id: str          # ebooklib 内部 item ID
    file_name: str        # 文件名（如 "chapter_001.xhtml"）
    char_count: int       # 字符数（纯文本）


@dataclass
class Section:
    """章节切分后的一个块，用于发送给 LLM 解读。"""

    chapter_index: int       # 所属章节序号
    chapter_title: str       # 所属章节标题
    section_index: int       # 块序号（从 0 开始）
    total_sections: int      # 该章总块数
    text: str                # 纯文本内容

    @property
    def id(self) -> str:
        """唯一标识，用于 checkpoint 查找。"""
        if self.total_sections == 1:
            return f"chapter_{self.chapter_index:03d}"
        return f"chapter_{self.chapter_index:03d}_section_{self.section_index}"

    @property
    def context_label(self) -> str:
        """上下文标签，注入到 LLM prompt 中。"""
        base = f"第{self.chapter_index + 1}章《{self.chapter_title}》"
        if self.total_sections > 1:
            return f"{base} 第 {self.section_index + 1}/{self.total_sections} 段"
        return base


# ---- EpubReader ----

class EpubReader:
    """读取 EPUB 文件，提取章节结构和文本内容。"""

    def __init__(self, epub_path: str | Path) -> None:
        self._path = Path(epub_path)
        self._book: epub.EpubBook | None = None
        self._chapters: list[Chapter] = []

    # ---- 公共 API ----

    @property
    def book(self) -> epub.EpubBook:
        """获取 ebooklib EpubBook 对象。"""
        if self._book is None:
            self._load()
        return self._book  # type: ignore[return-value]

    @property
    def chapters(self) -> list[Chapter]:
        """获取所有章节。"""
        if not self._chapters:
            self._load()
        return self._chapters

    @property
    def title(self) -> str:
        """获取书名。"""
        if self._book is None:
            self._load()
        title = self._book.title  # type: ignore[union-attr]
        if isinstance(title, (list, tuple)):
            return " ".join(str(t) for t in title)
        return str(title) if title else ""

    @property
    def total_chars(self) -> int:
        """获取全书总字符数。"""
        return sum(ch.char_count for ch in self.chapters)

    def get_chapter(self, index: int) -> Chapter | None:
        """按序号获取章节。"""
        chapters = self.chapters
        if 0 <= index < len(chapters):
            return chapters[index]
        return None

    def get_front_matter_text(self, max_chars: int = 3000) -> str:
        """获取前辅文文本（目录 + 前言 + 第一章），用于生成整书摘要。

        Args:
            max_chars: 最大字符数。

        Returns:
            前辅文的纯文本。
        """
        chapters = self.chapters
        if not chapters:
            return ""

        # 取前三章 + 如果有前言/导言类章节优先取
        parts: list[str] = []
        total = 0

        for ch in chapters:
            if total >= max_chars:
                break
            # 优先包含"前言""导言""序"等
            if any(kw in ch.title for kw in ("前言", "导言", "序", "引", "介绍")):
                parts.insert(0, f"# {ch.title}\n\n{ch.plain_text}")
            else:
                parts.append(f"# {ch.title}\n\n{ch.plain_text}")
            total += ch.char_count

        return "\n\n".join(parts)[:max_chars]

    # ---- 内部方法 ----

    def _load(self) -> None:
        """加载 EPUB 并解析章节。"""
        logger.info("正在加载 EPUB: %s", self._path)
        self._book = epub.read_epub(str(self._path), {"ignore_ncx": False})

        spine = list(self._book.spine)
        items = list(self._book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        # 建立 item id → item 的映射
        id_to_item: dict[str, Any] = {item.get_id(): item for item in self._book.get_items()}

        chapters: list[Chapter] = []
        chapter_index = 0

        for spine_id, _linear in spine:
            item = id_to_item.get(spine_id)
            if item is None:
                continue

            # 只处理文档类型
            if item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue

            # 跳过导航页（nav.xhtml / toc.ncx）
            file_name = (item.get_name() or "").lower()
            if file_name in ("nav.xhtml", "nav.html", "toc.xhtml", "toc.html"):
                continue

            content = item.get_content()
            if not content:
                continue

            html = content.decode("utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            # 跳过纯导航文档（内容主要是链接列表）
            nav_elem = soup.find("nav", attrs={"epub:type": "toc"})
            if nav_elem and len(soup.get_text(strip=True)) < 200:
                # 主要由导航链接构成，跳过
                continue

            # 提取纯文本
            plain_text = self._extract_plain_text(soup)
            if not plain_text.strip():
                # 跳过空文档（可能只有图片或样式）
                continue

            # 提取标题
            title = self._extract_title(soup, item, chapter_index)

            chapters.append(Chapter(
                index=chapter_index,
                title=title,
                content_html=html,
                plain_text=plain_text,
                item_id=spine_id,
                file_name=item.get_name() or f"chapter_{chapter_index:03d}.xhtml",
                char_count=len(plain_text),
            ))
            chapter_index += 1

        self._chapters = chapters
        logger.info("EPUB 加载完成: %d 个章节, 共 %d 字符", len(chapters), self.total_chars)

    @staticmethod
    def _extract_plain_text(soup: BeautifulSoup) -> str:
        """从 BeautifulSoup 对象中提取纯文本。

        移除脚本、样式、注释，保留段落结构。
        """
        # 移除 script 和 style
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()

        # 获取文本
        text = soup.get_text(separator="\n", strip=True)

        # 合并多余空行
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        return "\n".join(lines)

    @staticmethod
    def _extract_title(soup: BeautifulSoup, item: Any, index: int) -> str:
        """从文档中提取章节标题。

        优先级：<title> > <h1> > <h2> > item 的 title 属性 > 序号。
        """
        # 1. 尝试 <title> 标签
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            return _clean_title(title_tag.get_text(strip=True))

        # 2. 尝试 <h1>
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return _clean_title(h1.get_text(strip=True))

        # 3. 尝试 <h2>
        h2 = soup.find("h2")
        if h2 and h2.get_text(strip=True):
            return _clean_title(h2.get_text(strip=True))

        # 4. ebooklib item title
        if hasattr(item, "title") and item.title:
            return _clean_title(str(item.title))

        # 5. 兜底
        return f"第{index + 1}章"


# ---- EpubWriter ----

class EpubWriter:
    """将解读后的文本写回 EPUB，保留原书结构。"""

    def __init__(
        self,
        original_book: epub.EpubBook,
        chapters: list[Chapter] | None = None,
    ) -> None:
        """初始化。

        Args:
            original_book: 原书的 ebooklib EpubBook 对象。
            chapters: 从 EpubReader 获取的章节列表，用于准确匹配章节序号。
                      传入后 write() 通过 spine idref 精确匹配，而非靠正则猜测。
        """
        self._original = original_book
        self._chapters = chapters
        # 确保 title 是字符串（有些 EPUB 的 title 是列表）
        if isinstance(self._original.title, (list, tuple)):
            self._original.title = " ".join(str(t) for t in self._original.title)

    def write(
        self,
        output_path: str | Path,
        chapter_results: dict[int, str],  # chapter_index → interpreted_text
        title_suffix: str = "（解读版）",
    ) -> Path:
        """将解读后的章节内容写入新 EPUB。

        Args:
            output_path: 输出文件路径。
            chapter_results: 章节序号到解读后文本的映射。
            title_suffix: 书名后缀，用于区分原书。

        Returns:
            输出文件路径。
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 获取 spine 顺序和 item 映射
        spine = list(self._original.spine)
        id_to_item: dict[str, Any] = {
            item.get_id(): item for item in self._original.get_items()
        }

        # 构建 spine_id → chapter_index 精确映射（使用 chapters 中的 item_id）
        spine_to_chapter: dict[str, int] = {}
        if self._chapters:
            for ch in self._chapters:
                spine_to_chapter[ch.item_id] = ch.index

        updated_count = 0
        for spine_id, _linear in spine:
            item = id_to_item.get(spine_id)
            if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue

            # 优先通过 chapters 精确匹配，回退到正则猜测
            if self._chapters:
                chapter_idx = spine_to_chapter.get(spine_id)
            else:
                chapter_idx = self._find_chapter_index(item)

            if chapter_idx is not None and chapter_idx in chapter_results:
                interpreted_text = chapter_results[chapter_idx]
                new_html = self._text_to_html(interpreted_text, item)
                item.set_content(new_html.encode("utf-8"))
                updated_count += 1

        # 更新书名
        original_title = str(self._original.title) if self._original.title else "Untitled"
        self._original.set_title(f"{original_title}{title_suffix}")
        self._original.add_metadata("DC", "description", f"AI 解读版，原书：{original_title}")

        # 重新生成导航文件（NCX、NAV），确保目录引用正确
        has_ncx = any(
            getattr(item, 'file_name', '') == 'toc.ncx'
            for item in self._original.get_items()
        )
        has_nav = any(
            getattr(item, 'file_name', '') == 'nav.xhtml'
            for item in self._original.get_items()
        )
        if not has_ncx:
            self._original.add_item(epub.EpubNcx())
        if not has_nav:
            self._original.add_item(epub.EpubNav())

        # 写入
        epub.write_epub(str(output_path), self._original, {})
        logger.info(
            "EPUB 写入完成: %s（%d/%d 章已更新）",
            output_path,
            updated_count,
            len(chapter_results),
        )
        return output_path

    # ---- 内部方法 ----

    @staticmethod
    def _find_chapter_index(item: Any) -> int | None:
        """根据 item 推断章节序号。

        尝试多种匹配方式：文件名数字、item ID 数字 等。
        """
        import re

        file_name = item.get_name() or ""
        # 尝试匹配 "chapter_001" 这类文件名
        m = re.search(r"chapter[_\s]*(\d+)", file_name, re.IGNORECASE)
        if m:
            return int(m.group(1))

        # 尝试匹配 item id 中的数字
        item_id = item.get_id() or ""
        m = re.search(r"(\d+)", item_id)
        if m:
            return int(m.group(1))

        return None

    @staticmethod
    def _text_to_html(text: str, original_item: Any) -> str:
        """将纯文本转换为 HTML，尽可能保留原文档的结构框架。

        Args:
            text: 解读后的纯文本。
            original_item: 原始 ebooklib item（用于提取 HTML 框架）。

        Returns:
            HTML 字符串。
        """
        # 尝试提取原文档的 HTML 结构
        try:
            original_html = original_item.get_content().decode("utf-8", errors="replace")
        except Exception:
            original_html = ""

        soup = BeautifulSoup(original_html or "<html><body></body></html>", "html.parser")

        # 找到 body 标签
        body = soup.find("body")
        if body is None:
            body = soup

        # 保留 head（包含 CSS 引用），但清空 body 内容
        # 将解读文本按段落分割为 <p> 标签
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # 清空 body 中除 h1/h2/h3 以外的内容
        headings = []
        for tag in body.find_all(["h1", "h2", "h3"]):
            headings.append(tag.extract())

        body.clear()

        # 恢复标题
        for heading in headings:
            body.append(heading)

        # 添加内容段落
        for para in paragraphs:
            p = soup.new_tag("p")
            p.string = para
            body.append(p)

        return str(soup)


# ---- 工具函数 ----

def _clean_title(title: str) -> str:
    """清理章节标题。"""
    # 移除多余空白
    title = " ".join(title.split())
    # 截断过长的标题
    if len(title) > 100:
        title = title[:100] + "…"
    return title
