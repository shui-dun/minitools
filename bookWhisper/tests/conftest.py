"""测试共享 fixtures。

提供各模块测试所需的：
- 临时目录
- 真实 EPUB（金枝，73 章，约 64 万字符）
- 真实 MOBI（精神现象学(上册)，用于格式转换测试）
- 真实 AZW3（阿奎那政治著作选，用于格式转换测试）
- 测试用合成 EPUB（2 章，内容可控，用于边界条件测试）
- 配置对象
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from ebooklib import epub

# 真实测试用书路径
_REAL_EPUB_PATH = Path(__file__).parent / "data" / "金枝.epub"
_REAL_MOBI_PATH = Path(__file__).parent / "data" / "精神现象学(上册) (汉译世界学术名著丛书) - 黑格尔.mobi"
_REAL_AZW3_PATH = Path(__file__).parent / "data" / "阿奎那政治著作选 (汉译世界学术名著丛书) - 阿奎那.azw3"


@pytest.fixture
def tmp_dir() -> Path:
    """临时工作目录，测试结束后自动清理。"""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


# ==================== 真实 EPUB fixture ====================


@pytest.fixture(scope="session")
def real_epub_path() -> Path:
    """真实 EPUB 书籍《金枝》（73 章，约 64 万字符）。

    用于集成测试，验证代码对真实电子书的处理能力。
    """
    if not _REAL_EPUB_PATH.exists():
        pytest.skip(f"真实测试 EPUB 不存在: {_REAL_EPUB_PATH}")
    return _REAL_EPUB_PATH


@pytest.fixture(scope="session")
def real_mobi_path() -> Path:
    """真实 MOBI 书籍《精神现象学(上册)》（约 1.9 MB）。

    用于测试 MOBI 格式的识别和转换功能。
    """
    if not _REAL_MOBI_PATH.exists():
        pytest.skip(f"真实测试 MOBI 不存在: {_REAL_MOBI_PATH}")
    return _REAL_MOBI_PATH


@pytest.fixture(scope="session")
def real_azw3_path() -> Path:
    """真实 AZW3 书籍《阿奎那政治著作选》（约 0.5 MB）。

    用于测试 AZW3 格式的识别和转换功能。
    """
    if not _REAL_AZW3_PATH.exists():
        pytest.skip(f"真实测试 AZW3 不存在: {_REAL_AZW3_PATH}")
    return _REAL_AZW3_PATH


@pytest.fixture(scope="session")
def real_reader(real_epub_path: Path):
    """基于真实 EPUB 的 EpubReader 实例（session 级别，避免重复解析）。"""
    from bookwhisper.epub_processor import EpubReader

    return EpubReader(real_epub_path)


# ==================== 合成 EPUB fixture（用于边界测试） ====================


@pytest.fixture
def sample_epub_path(tmp_dir: Path) -> Path:
    """构造一个简单的测试 EPUB（2 章），用于边界条件测试。

    第 1 章：短章节（约 150 字符）
    第 2 章：长章节（约 800 字符，用于测试切分）
    """
    book = epub.EpubBook()
    book.set_identifier("test-book-001")
    book.set_title("测试书籍")
    book.set_language("zh")
    book.add_author("测试作者")

    # 样式
    style = "p { margin: 0.5em 0; } h1 { font-size: 1.5em; }"
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style.encode("utf-8"),
    )
    book.add_item(nav_css)

    # 第 1 章（短）
    ch1 = epub.EpubHtml(
        title="第一章 引言",
        file_name="chapter_001.xhtml",
        lang="zh",
    )
    ch1_content = """<html><head><title>第一章 引言</title></head><body>
    <h1>第一章 引言</h1>
    <p>这是一本关于社会科学理论的测试书籍。</p>
    <p>本章将介绍几个核心概念，为后续讨论做铺垫。</p>
    <p>在现代社会中，人们对于知识的获取方式正在发生深刻变化。</p>
</body></html>"""
    ch1.set_content(ch1_content.encode("utf-8"))
    book.add_item(ch1)

    # 第 2 章（长，用于测试分块）
    ch2 = epub.EpubHtml(
        title="第二章 深度分析",
        file_name="chapter_002.xhtml",
        lang="zh",
    )
    long_text = "第二章 深度分析\n\n"
    long_text += "值得注意的是，在相当多的学术话语场域中，哈贝马斯所提出的交往理性这一概念，在某种意义上可以被视为是对韦伯目的理性批判性重构的理论尝试。\n\n"
    long_text += "学术界对此展开了热烈讨论。有学者认为，这种解读过于简单化，未能充分考虑到历史语境的影响。然而，另一些研究者则指出，如果我们从更宏观的视角来看待这个问题，就会发现哈贝马斯的理论创新恰恰在于他将语言学转向引入了批判理论的传统之中。\n\n"
    long_text += "为了更深入地理解这一点，我们需要回顾一下二十世纪哲学的发展脉络。从胡塞尔的现象学，到海德格尔的存在论，再到伽达默尔的诠释学，一条清晰的理论演进线索呈现在我们面前。哈贝马斯正是在这个传统中找到了自己的理论位置。\n\n"
    ch2_content = f"<html><head><title>第二章 深度分析</title></head><body><h1>第二章 深度分析</h1><p>{long_text.replace(chr(10), '</p><p>')}</p></body></html>"
    ch2.set_content(ch2_content.encode("utf-8"))
    book.add_item(ch2)

    # Spine
    book.spine = ["nav", ch1, ch2]

    # ToC
    book.toc = [
        epub.Link("chapter_001.xhtml", "第一章 引言", "ch1"),
        epub.Link("chapter_002.xhtml", "第二章 深度分析", "ch2"),
    ]

    # 添加导航
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 写入
    output_path = tmp_dir / "sample.epub"
    epub.write_epub(str(output_path), book, {})
    return output_path


@pytest.fixture
def sample_config():
    """创建测试用的 AppConfig（全部默认值）。"""
    from bookwhisper.config import AppConfig

    return AppConfig()
