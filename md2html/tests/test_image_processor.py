"""
图片链接转换的单元测试。
"""

from pathlib import Path

from image_processor import build_image_table, fix_image_links


class TestBuildImageTable:
    """build_image_table 函数测试。"""

    def test_basic(self, tmp_notes_dir):
        """扫描目录，验证哈希表格式。"""
        table = build_image_table(str(tmp_notes_dir), [])
        assert "photo.png" in table
        assert "logo.svg" in table
        assert "中文图片.jpg" in table
        # 值是绝对路径
        assert Path(table["photo.png"]).is_absolute()

    def test_duplicate_name(self, tmp_notes_dir, capsys):
        """同名图片只保留先发现的，后发现的打印警告。"""
        # 在子目录也放一个同名图片
        (tmp_notes_dir / "subdir" / "photo.png").touch()
        table = build_image_table(str(tmp_notes_dir), [])
        # 保留先发现的（根目录的）
        captured = capsys.readouterr()
        assert "重名图片文件 'photo.png'" in captured.out
        # 值指向先发现的路径
        assert str(Path(table["photo.png"]).parent) == str(tmp_notes_dir)

    def test_excludes_non_image_files(self, tmp_notes_dir):
        """非图片文件不出现在哈希表中。"""
        table = build_image_table(str(tmp_notes_dir), [])
        assert "index.md" not in table
        assert "note_a.md" not in table


class TestFixImageLinks:
    """fix_image_links 函数测试。"""

    def test_standard_image(self, tmp_notes_dir):
        """标准 Markdown 图片语法：![alt](image.png) → ![alt](/assets/image.png)。"""
        md = tmp_notes_dir / "index.md"
        md.write_text("![pic](photo.png)", encoding="utf-8")
        table = build_image_table(str(tmp_notes_dir), [])
        used: set[str] = set()

        fix_image_links(md, table, used)

        result = md.read_text(encoding="utf-8")
        assert result == "![pic](/assets/photo.png)"
        assert "photo.png" in used

    def test_standard_image_external(self, tmp_notes_dir):
        """外部链接（http/https）跳过不处理。"""
        md = tmp_notes_dir / "index.md"
        md.write_text("![pic](https://example.com/img.png)", encoding="utf-8")
        table = build_image_table(str(tmp_notes_dir), [])
        used: set[str] = set()

        fix_image_links(md, table, used)

        result = md.read_text(encoding="utf-8")
        assert "https://example.com/img.png" in result

    def test_standard_image_not_found(self, tmp_notes_dir, capsys):
        """不存在的图片保留原文并打印警告。"""
        md = tmp_notes_dir / "index.md"
        md.write_text("![pic](ghost.png)", encoding="utf-8")
        table = build_image_table(str(tmp_notes_dir), [])
        used: set[str] = set()

        fix_image_links(md, table, used)

        result = md.read_text(encoding="utf-8")
        assert "ghost.png" in result  # 保留原文
        captured = capsys.readouterr()
        assert "找不到图片" in captured.out

    def test_obsidian_image(self, tmp_notes_dir):
        """Obsidian wikilink 图片语法：![[image.png]] → ![](/assets/image.png)。"""
        md = tmp_notes_dir / "Note B.md"
        table = build_image_table(str(tmp_notes_dir), [])
        used: set[str] = set()

        fix_image_links(md, table, used)

        result = md.read_text(encoding="utf-8")
        assert "![](/assets/logo.svg)" in result
        assert "logo.svg" in used

    def test_obsidian_image_chinese_filename(self, tmp_notes_dir):
        """Obsidian wikilink 图片语法，中文文件名（含路径前缀 ../）。"""
        # 在子目录创建一个引用中文图片的文件
        md = tmp_notes_dir / "subdir" / "test_chinese.md"
        md.write_text("![[../中文图片.jpg]]", encoding="utf-8")
        table = build_image_table(str(tmp_notes_dir), [])
        used: set[str] = set()

        fix_image_links(md, table, used)

        result = md.read_text(encoding="utf-8")
        assert "中文图片.jpg" in used
        assert "/assets/" in result

    def test_both_image_syntaxes(self, tmp_notes_dir):
        """同一文件同时包含标准语法和 wikilink 语法的图片引用。"""
        md = tmp_notes_dir / "index.md"
        md.write_text("![a](photo.png)\n\n![[logo.svg]]", encoding="utf-8")
        table = build_image_table(str(tmp_notes_dir), [])
        used: set[str] = set()

        fix_image_links(md, table, used)

        result = md.read_text(encoding="utf-8")
        assert "![a](/assets/photo.png)" in result
        assert "![](/assets/logo.svg)" in result
        assert "photo.png" in used
        assert "logo.svg" in used
