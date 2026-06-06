"""
共享的 pytest fixture（测试上下文环境）。
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_notes_dir():
    """
    创建临时笔记目录，预设若干 .md 文件和图片文件。

    目录结构:
        notes/
        ├── index.md
        ├── Note A.md
        ├── Note B.md
        ├── subdir/
        │   ├── Note C.md
        │   └── Deep Note.md
        ├── photo.png
        ├── logo.svg
        └── 中文图片.jpg
    """
    tmp = Path(tempfile.mkdtemp())
    notes = tmp / "notes"
    notes.mkdir()

    # 创建子目录
    subdir = notes / "subdir"
    subdir.mkdir()

    # 创建 .md 文件（文件名 stem 与 wikilink 中的笔记名一致）
    (notes / "index.md").write_text("# 首页\n\n[[Note A]]\n\n![图片](photo.png)", encoding="utf-8")
    (notes / "Note A.md").write_text("# Note A\n\n[[Note B|B笔记]]\n\n[[Note C]]", encoding="utf-8")
    (notes / "Note B.md").write_text("# Note B\n\n![[logo.svg]]\n\n[[Note A#简介]]", encoding="utf-8")
    (subdir / "Note C.md").write_text("# Note C\n\n[[Note A]]", encoding="utf-8")
    (subdir / "Deep Note.md").write_text("# Deep Note\n\n[[Note A#安装|安装说明]]", encoding="utf-8")

    # 创建图片文件（空文件即可，测试不需要真实内容）
    (notes / "photo.png").touch()
    (notes / "logo.svg").touch()
    (notes / "中文图片.jpg").touch()

    return notes
