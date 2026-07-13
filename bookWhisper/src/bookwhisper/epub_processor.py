"""EPUB 处理模块。

基于 ebooklib + BeautifulSoup 实现：
- EpubReader：读取 EPUB，提取章节结构和正文文本
- EpubWriter：创建新的 EPUB，继承原书元数据和封面图，使用解读后的章节文本
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
    """用解读后的文本创建全新的 EPUB，仅继承原书的元数据和封面图。
    章节标题使用 EpubReader 已正确解析的 Chapter.title，
    章节内容从 chapter_results（来自缓存/checkpoint）读取。
    """

    def __init__(
        self,
        original_book: epub.EpubBook,
        chapters: list[Chapter],
    ) -> None:
        """初始化。

        Args:
            original_book: 原书的 ebooklib EpubBook 对象，用于提取元数据和封面图。
            chapters: 从 EpubReader 获取的章节列表，提供正确的章节标题。
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
        """将解读后的章节内容写入全新的 EPUB 文件。

        Args:
            output_path: 输出文件路径。
            chapter_results: 章节序号到解读后文本的映射。
            title_suffix: 书名后缀，用于区分原书。

        Returns:
            输出文件路径。
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        new_book = self._build_book(chapter_results, title_suffix)

        epub.write_epub(str(output_path), new_book, {})
        logger.info(
            "EPUB 写入完成: %s（%d/%d 章已输出）",
            output_path,
            len([ch for ch in self._chapters if ch.index in chapter_results]),
            len(chapter_results),
        )
        return output_path

    # ---- 内部方法 ----

    def _build_book(
        self,
        chapter_results: dict[int, str],
        title_suffix: str,
    ) -> epub.EpubBook:
        """从零构建全新的 EpubBook。

        Args:
            chapter_results: 章节序号到解读后文本的映射。
            title_suffix: 书名后缀。

        Returns:
            全新的 epub.EpubBook 对象。
        """
        # 1. 创建空书
        new_book = epub.EpubBook()

        # 2. 复制元数据
        self._copy_metadata(new_book)

        # 3. 设置带后缀的书名
        original_title = str(self._original.title) if self._original.title else "Untitled"
        new_book.set_title(f"{original_title}{title_suffix}")
        new_book.add_metadata("DC", "description", f"AI 解读版，原书：{original_title}")

        # 4. 复制封面图
        self._copy_cover(new_book)

        # 5. 获取原书语言，用于章节 HTML 的 lang 属性
        lang = self._original.language or "zh-CN"

        # 6. 为每个有解读结果的章节创建 EpubHtml
        chapter_items: list[epub.EpubHtml] = []
        for ch in self._chapters:
            if ch.index not in chapter_results:
                continue

            interpreted_text = chapter_results[ch.index]
            html_content = self._build_chapter_html(ch.title, interpreted_text, lang)

            file_name = f"chapter_{ch.index:03d}.xhtml"
            epub_chapter = epub.EpubHtml(
                title=ch.title,
                file_name=file_name,
                lang=lang,
            )
            epub_chapter.set_content(html_content.encode("utf-8"))
            new_book.add_item(epub_chapter)
            chapter_items.append(epub_chapter)

        # 7. 构建 spine 和 ToC
        self._build_spine_and_toc(new_book, chapter_items)

        # 8. 添加导航文件
        new_book.add_item(epub.EpubNcx())
        new_book.add_item(epub.EpubNav())

        return new_book

    def _copy_metadata(self, new_book: epub.EpubBook) -> None:
        """从原书复制 DC 元数据到新书。

        复制 creator、language、publisher、date、identifier 等字段。
        跳过 title（由 set_title 单独处理）和 OPF namespace（ebooklib 自动生成）。
        """
        # 安全获取元数据：部分 EPUB 可能缺少某个 namespace
        def _safe_get_metadata(namespace: str, name: str) -> list[tuple[Any, Any]]:
            try:
                return self._original.get_metadata(namespace, name)
            except KeyError:
                return []

        # 作者：第一个用 add_author，其余用 add_metadata
        creators = _safe_get_metadata("DC", "creator")
        for i, (value, attrs) in enumerate(creators):
            if i == 0:
                new_book.add_author(str(value), uid=str(attrs.get("id", "creator")))
            else:
                new_book.add_metadata("DC", "creator", str(value), attrs)

        # 语言
        lang_entries = _safe_get_metadata("DC", "language")
        for value, _attrs in lang_entries:
            new_book.set_language(str(value))
            break  # 只取第一个

        # 标识符
        identifiers = _safe_get_metadata("DC", "identifier")
        for value, attrs in identifiers:
            if attrs.get("id") == self._original.IDENTIFIER_ID:
                new_book.set_identifier(str(value))
                break
        else:
            # 没有带主标识符 ID 的，取第一个
            for value, _attrs in identifiers:
                new_book.set_identifier(str(value))
                break

        # 其他 DC 字段
        dc_fields = [
            "publisher", "date", "subject", "contributor",
            "rights", "type", "format", "source", "relation", "coverage",
        ]
        for field in dc_fields:
            entries = _safe_get_metadata("DC", field)
            for value, attrs in entries:
                new_book.add_metadata("DC", field, str(value), attrs)

    def _copy_cover(self, new_book: epub.EpubBook) -> None:
        """从原书复制封面图到新书。

        按优先级查找：ITEM_COVER > ITEM_IMAGE(cover-image) > meta cover。
        找不到封面时静默跳过。
        """
        # 优先级 1：ITEM_COVER（ebooklib 读取时自动标记）
        cover_items = list(self._original.get_items_of_type(ebooklib.ITEM_COVER))
        if cover_items:
            cover = cover_items[0]
            new_book.set_cover(
                cover.get_name() or "cover.jpg",
                cover.get_content(),
                create_page=True,
            )
            logger.info("已从原书复制封面图（ITEM_COVER）。")
            return

        # 优先级 2：ITEM_IMAGE 中带 "cover-image" 属性的
        for item in self._original.get_items_of_type(ebooklib.ITEM_IMAGE):
            props: list[str] = getattr(item, "properties", []) or []
            if "cover-image" in props:
                new_book.set_cover(
                    item.get_name() or "cover.jpg",
                    item.get_content(),
                    create_page=True,
                )
                logger.info("已从原书复制封面图（cover-image 属性）。")
                return

        # 优先级 3：<meta name="cover" content="xxx"/> 中指定的 cover image ID
        # 注意：部分 EPUB 的 metadata 中没有 None namespace，需安全访问
        try:
            metas = self._original.get_metadata(None, "meta")
        except KeyError:
            metas = []
        for _value, attrs in metas:
            if attrs.get("name") == "cover":
                cover_item_id = attrs.get("content", "")
                if cover_item_id:
                    try:
                        cover_item = self._original.get_item_with_id(cover_item_id)
                        if cover_item is not None:
                            new_book.set_cover(
                                cover_item.get_name() or "cover.jpg",
                                cover_item.get_content(),
                                create_page=True,
                            )
                            logger.info("已从原书复制封面图（meta cover）。")
                            return
                    except Exception:
                        pass
                break

        logger.info("原书未找到封面图片，输出 EPUB 将不含封面。")

    @staticmethod
    def _build_chapter_html(title: str, text: str, lang: str = "zh-CN") -> str:
        """生成干净的章节 HTML，不继承原书的任何结构/CSS。

        Args:
            title: 章节标题。
            text: 解读后的纯文本。
            lang: 语言代码。

        Returns:
            完整的 XHTML 字符串。
        """
        import html as html_module

        escaped_title = html_module.escape(title)

        # 按空行分段
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        para_html = "\n".join(
            f"  <p>{html_module.escape(p)}</p>" for p in paragraphs
        )

        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml"'
            ' xmlns:epub="http://www.idpf.org/2007/ops"'
            f' lang="{html_module.escape(lang)}">\n'
            '<head>\n'
            f'  <title>{escaped_title}</title>\n'
            '  <meta charset="utf-8"/>\n'
            '</head>\n'
            '<body>\n'
            f'  <h1>{escaped_title}</h1>\n'
            f'{para_html}\n'
            '</body>\n'
            '</html>'
        )

    @staticmethod
    def _build_spine_and_toc(
        new_book: epub.EpubBook,
        chapter_items: list[epub.EpubHtml],
    ) -> None:
        """为新书构建 spine 和 ToC。

        cover 页和 nav 页设为 non-linear，章节按顺序排列。

        Args:
            new_book: 正在构建的新书。
            chapter_items: 已添加的章节 EpubHtml 列表。
        """
        spine: list[Any] = []
        toc: list[epub.Link] = []

        # cover 页（如存在）设为 non-linear
        for item in new_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            if isinstance(item, epub.EpubCoverHtml):
                spine.append((item, "no"))
                break

        # nav 页设为 non-linear
        for item in new_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            if isinstance(item, epub.EpubNav):
                spine.append((item, "no"))
                break

        # 各章节
        for ch_item in chapter_items:
            spine.append(ch_item)
            toc.append(epub.Link(
                href=ch_item.file_name,
                title=ch_item.title,
                uid=ch_item.get_id(),
            ))

        new_book.spine = spine
        new_book.toc = toc


# ---- 工具函数 ----

def _clean_title(title: str) -> str:
    """清理章节标题。"""
    # 移除多余空白
    title = " ".join(title.split())
    # 截断过长的标题
    if len(title) > 100:
        title = title[:100] + "…"
    return title
