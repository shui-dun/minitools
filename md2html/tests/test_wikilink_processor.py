"""
wikilink 笔记链接转换的单元测试。
"""

from pathlib import Path

from wikilink_processor import (
    WIKILINK_RE,
    build_note_table,
    fix_wikilinks,
    _compute_relative_link,
)


class TestBuildNoteTable:
    """build_note_table 函数测试。"""

    def test_basic(self, tmp_notes_dir):
        """扫描目录，验证 {笔记名: 相对路径} 格式。"""
        table = build_note_table(str(tmp_notes_dir), [])
        assert table["index"] == Path("index.md")
        assert table["Note A"] == Path("Note A.md")
        assert table["Note B"] == Path("Note B.md")
        assert table["Note C"] == Path("subdir/Note C.md")
        assert table["Deep Note"] == Path("subdir/Deep Note.md")

    def test_duplicate_name(self, tmp_notes_dir, capsys):
        """同名笔记只保留先发现的，后发现的打印警告。"""
        # 在子目录也放一个同名笔记
        (tmp_notes_dir / "subdir" / "Note A.md").write_text("# Duplicate", encoding="utf-8")
        table = build_note_table(str(tmp_notes_dir), [])
        captured = capsys.readouterr()
        assert "重名笔记文件 'Note A'" in captured.out
        # 保留先发现的（根目录的）
        assert table["Note A"] == Path("Note A.md")

    def test_excludes_non_md_files(self, tmp_notes_dir):
        """非 .md 文件不出现在哈希表中。"""
        table = build_note_table(str(tmp_notes_dir), [])
        assert "photo" not in table
        assert "logo" not in table


class TestRegex:
    """WIKILINK_RE 正则表达式测试。"""

    def test_simple(self):
        """[[Note]] — 基本 wikilink。"""
        m = WIKILINK_RE.search("[[Python]]")
        assert m is not None
        assert m.group(1) == "Python"
        assert m.group(2) is None
        assert m.group(3) is None

    def test_with_alias(self):
        """[[Note|别名]] — 带别名的 wikilink。"""
        m = WIKILINK_RE.search("[[Python|Python语言]]")
        assert m is not None
        assert m.group(1) == "Python"
        assert m.group(2) is None
        assert m.group(3) == "Python语言"

    def test_with_anchor(self):
        """[[Note#标题]] — 带标题锚点的 wikilink。"""
        m = WIKILINK_RE.search("[[Python#安装指南]]")
        assert m is not None
        assert m.group(1) == "Python"
        assert m.group(2) == "安装指南"
        assert m.group(3) is None

    def test_with_anchor_and_alias(self):
        """[[Note#标题|别名]] — 同时带锚点和别名。"""
        m = WIKILINK_RE.search("[[Python#虚拟环境|venv用法]]")
        assert m is not None
        assert m.group(1) == "Python"
        assert m.group(2) == "虚拟环境"
        assert m.group(3) == "venv用法"


class TestComputeRelativeLink:
    """_compute_relative_link 函数测试。"""

    def test_same_directory(self):
        """同目录下直接返回文件名。"""
        result = _compute_relative_link(
            Path("tech/Python.md"),
            Path("tech/Django.md"),
        )
        assert result == "Django.md"

    def test_sub_directory(self):
        """目标在子目录中。"""
        result = _compute_relative_link(
            Path("index.md"),
            Path("tech/Python.md"),
        )
        assert result == "tech/Python.md"

    def test_parent_directory(self):
        """目标在父目录中。"""
        result = _compute_relative_link(
            Path("tech/deep/Python.md"),
            Path("index.md"),
        )
        assert result == "../../index.md"

    def test_sibling_directory(self):
        """目标在兄弟目录中。"""
        result = _compute_relative_link(
            Path("tech/Python.md"),
            Path("life/Travel.md"),
        )
        assert result == "../life/Travel.md"


class TestFixWikilinks:
    """fix_wikilinks 函数测试。"""

    def test_simple_wikilink(self, tmp_notes_dir):
        """[[Note]] → [Note](Note)。"""
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "index.md"
        # index.md 包含 [[Note A]]，Note A.md 在根目录
        fix_wikilinks(md, table, Path("index.md"))

        result = md.read_text(encoding="utf-8")
        assert "[Note A](Note A.md)" in result

    def test_wikilink_with_alias(self, tmp_notes_dir):
        """[[Note|别名]] → [别名](Note)。"""
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "Note A.md"
        # Note A.md 包含 [[Note B|B笔记]]

        fix_wikilinks(md, table, Path("Note A.md"))

        result = md.read_text(encoding="utf-8")
        assert "[B笔记](Note B.md)" in result

    def test_wikilink_with_anchor(self, tmp_notes_dir):
        """[[Note#标题]] → [Note#标题](Note#标题)。"""
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "Note B.md"
        # Note B.md 包含 [[Note A#简介]]

        fix_wikilinks(md, table, Path("Note B.md"))

        result = md.read_text(encoding="utf-8")
        assert "[Note A#简介](Note A.md#简介)" in result

    def test_wikilink_with_anchor_and_alias(self, tmp_notes_dir):
        """[[Note#标题|别名]] → [别名](Note#标题)。"""
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "subdir" / "Deep Note.md"
        # Deep Note.md 包含 [[Note A#安装|安装说明]]

        fix_wikilinks(md, table, Path("subdir/Deep Note.md"))

        result = md.read_text(encoding="utf-8")
        # Deep Note.md 在 subdir/，Note A.md 在根目录，相对路径为 ../Note A
        assert "[安装说明](../Note A.md#安装)" in result

    def test_wikilink_not_found(self, tmp_notes_dir, capsys):
        """不存在的笔记保留原文并打印警告。"""
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "index.md"
        md.write_text("[[GhostNote]]", encoding="utf-8")

        fix_wikilinks(md, table, Path("index.md"))

        result = md.read_text(encoding="utf-8")
        assert "[[GhostNote]]" in result  # 保留原文
        captured = capsys.readouterr()
        assert "找不到笔记链接目标" in captured.out

    def test_cross_directory_link(self, tmp_notes_dir):
        """跨目录链接路径正确：subdir/Note C.md 引用根目录的 Note A。"""
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "subdir" / "Note C.md"
        # Note C.md 在 subdir/，引用根目录的 [[Note A]]
        # 相对路径应为 ../Note A

        fix_wikilinks(md, table, Path("subdir/Note C.md"))

        result = md.read_text(encoding="utf-8")
        assert "[Note A](../Note A.md)" in result

    def test_image_wikilink_not_affected(self, tmp_notes_dir):
        """
        ![[image.png]] 的处理在 fix_image_links 中已完成。
        此处验证 fix_wikilinks 不会产生副作用：
        Note B.md 包含 ![[logo.svg]]，先用 fix_image_links 处理，
        再用 fix_wikilinks 处理，wikilink 正则不应再误匹配。
        """
        table = build_note_table(str(tmp_notes_dir), [])
        md = tmp_notes_dir / "Note B.md"
        # Note B.md 原始内容有 ![[logo.svg]]（图片 wikilink）

        # 先模拟 fix_image_links 的效果：将 ![[logo.svg]] 转为 ![](/assets/logo.svg)
        from image_processor import fix_image_links
        from image_processor import build_image_table as build_img_table

        img_table = build_img_table(str(tmp_notes_dir), [])
        used: set[str] = set()
        fix_image_links(md, img_table, used)

        # 现在 Note B.md 中不应再有 ![[logo.svg]]
        # fix_wikilinks 处理时也不应有任何变化
        fix_wikilinks(md, table, Path("Note B.md"))

        result = md.read_text(encoding="utf-8")
        # logo 已被图片处理转为 /assets/ 路径，wikilink 正则匹配不到
        assert "![[logo.svg]]" not in result
