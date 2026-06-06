"""
处理 Obsidian wikilink [[笔记链接]] 到标准 Markdown 链接的转换。
"""

import os
import re
from pathlib import Path

# =============================================================================
# 常量
# =============================================================================

# 匹配 Obsidian wikilink 笔记链接语法 [[笔记名]]、[[笔记名|别名]]、[[笔记名#标题]]
WIKILINK_RE = re.compile(
    r"\[\["
    r"([^\]|#]+)"             # group(1): 笔记名（必选）
    r"(?:#([^\]|]*))?"        # group(2): 锚点/标题（可选）
    r"(?:\|([^\]]+))?"        # group(3): 显示别名（可选）
    r"\]\]"
)


# =============================================================================
# 笔记哈希表
# =============================================================================


def build_note_table(notes_dir: str, ignore_dirs: list[str]) -> dict[str, Path]:
    """
    遍历笔记目录，返回 {笔记名: 相对路径} 的哈希表。

    笔记名为 .md 文件名去掉扩展名。同名笔记使用先发现的版本，打印警告。
    """
    notes_path = Path(notes_dir)
    table: dict[str, Path] = {}

    for root, dirs, files in os.walk(notes_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        files[:] = [f for f in files if f not in ignore_dirs]

        for fname in files:
            if not fname.endswith(".md"):
                continue

            note_name = Path(fname).stem  # 去掉 .md 扩展名
            src = Path(root) / fname
            rel = src.relative_to(notes_path)

            if note_name in table:
                print(f"   ⚠  重名笔记文件 '{note_name}' — 使用先找到的：")
                print(f"      {notes_path / table[note_name]}")
                print(f"      {src}")
            else:
                table[note_name] = rel

    return table


# =============================================================================
# wikilink 修复
# =============================================================================


def _compute_relative_link(src_md_rel: Path, target_md_rel: Path) -> str:
    """计算从源 .md 到目标 .md 的相对链接路径。"""
    src_dir = src_md_rel.parent
    rel = os.path.relpath(str(target_md_rel), str(src_dir))
    return rel.replace("\\", "/")


def fix_wikilinks(
    md_path: Path,
    note_table: dict[str, Path],
    md_rel: Path,
) -> None:
    """
    读取 Markdown 文件，将 [[笔记名]]、[[笔记名|别名]]、[[笔记名#标题]] 等
    Obsidian wikilink 语法替换为标准 Markdown 链接。

    md_rel: 当前 .md 文件相对于笔记根目录的路径（如 Path("技术/Python.md")）。
    """
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception:
        return

    def _replace_wikilink(match: re.Match) -> str:
        note_name = match.group(1)
        anchor = match.group(2) or ""
        alias = match.group(3) or ""

        if note_name not in note_table:
            _warn_note_not_found(md_path, note_name)
            return match.group(0)

        target_rel = note_table[note_name]
        link_path = _compute_relative_link(md_rel, target_rel)


        # 锚点追加
        if anchor:
            link_path += "#" + anchor.lower().replace(" ", "-")

        # 显示文本：优先别名，其次 笔记名#标题，最后笔记名
        if alias:
            display = alias
        elif anchor:
            display = f"{note_name}#{anchor}"
        else:
            display = note_name

        return f"[{display}]({link_path})"

    new_content = WIKILINK_RE.sub(_replace_wikilink, content)

    if new_content != content:
        md_path.write_text(new_content, encoding="utf-8")


def _warn_note_not_found(md_path: Path, note_name: str) -> None:
    """打印找不到笔记的警告。"""
    try:
        rel = md_path.relative_to(Path.cwd())
    except ValueError:
        rel = md_path
    print(f"   ⚠  找不到笔记链接目标: '[[{note_name}]]'  ←  {rel}")
