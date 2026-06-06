"""
处理 Markdown 文件中图片链接的核心逻辑。
"""

import os
import re
import urllib.parse
from pathlib import Path

# =============================================================================
# 常量
# =============================================================================

# 常见的图片文件后缀
IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"})

# 匹配 Markdown 标准图片语法 ![alt](url)
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# 匹配 Obsidian wikilink 图片语法 ![[image.png]]
OBSIDIAN_IMAGE_RE = re.compile(
    r"!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|svg|webp|bmp|ico))\]\]",
    re.IGNORECASE,
)


# =============================================================================
# 图片哈希表
# =============================================================================


def build_image_table(notes_dir: str, ignore_dirs: list[str]) -> dict[str, str]:
    """
    遍历笔记目录，返回 {文件名: 绝对路径} 的哈希表。
    """
    table: dict[str, str] = {}

    for root, dirs, files in os.walk(notes_dir):
        # --- 排除忽略的目录和文件 ---
        # os.walk 的 topdown 模式（默认）会先访问父目录再访问子目录。
        # 在这里修改 dirs 列表，os.walk 就会按修改后的列表决定下一步进入哪些子目录。
        # dirs[:] = [新列表] → 原地替换同一个列表对象的内容。
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        files[:] = [f for f in files if f not in ignore_dirs]

        # --- 收集当前目录下的图片文件 ---
        for fname in files:
            if Path(fname).suffix.lower() not in IMAGE_EXTS:
                continue

            # 处理同名图片：用先发现的版本，后发现的打印警告但不覆盖
            if fname in table:
                print(f"   ⚠  重名图片文件 '{fname}' — 使用先找到的：")
                print(f"      {table[fname]}")
                print(f"      {os.path.join(root, fname)}")
            else:
                table[fname] = os.path.join(root, fname)

    return table


# =============================================================================
# 图片链接修复
# =============================================================================


def fix_image_links(
    md_path: Path,
    image_table: dict[str, str],
    used_images: set[str],
) -> None:
    """
    读取 Markdown 文件，将本地图片引用替换为 /assets/filename 格式。
    """
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception:
        return

    def _replace_standard_image(match: re.Match) -> str:
        """
        处理标准 Markdown 图片语法：![alt](url)
        """
        alt = match.group(1)
        raw_url = match.group(2)

        # 外部链接（http/https）直接跳过，不修改
        if raw_url.startswith(("http://", "https://")):
            return match.group(0)

        # URL 解码：将 %xx 编码还原为原始字符（中文路径经常被编码）
        decoded = urllib.parse.unquote(raw_url)
        # 只取文件名部分，丢弃前面的目录路径
        filename = Path(decoded).name

        if filename in image_table:
            used_images.add(filename)
            safe_name = urllib.parse.quote(filename)
            return f"![{alt}](/assets/{safe_name})"

        _warn_not_found(md_path, filename)
        return match.group(0)

    def _replace_obsidian_image(match: re.Match) -> str:
        """
        处理 Obsidian wikilink 图片语法：![[image.png]]
        """
        raw = match.group(1)  # wiki链接不需要解码，但可能包含路径前缀如 ../xxx.png
        filename = Path(raw).name  # 只取文件名部分，丢弃目录路径
        if filename in image_table:
            used_images.add(filename)
            safe_name = urllib.parse.quote(filename)
            return f"![](/assets/{safe_name})"

        _warn_not_found(md_path, filename)
        return match.group(0)

    new_content = MD_IMAGE_RE.sub(_replace_standard_image, content)
    new_content = OBSIDIAN_IMAGE_RE.sub(_replace_obsidian_image, new_content)

    if new_content != content:
        md_path.write_text(new_content, encoding="utf-8")


def _warn_not_found(md_path: Path, filename: str) -> None:
    """打印找不到图片的警告。"""
    try:
        rel = md_path.relative_to(Path.cwd())
    except ValueError:
        rel = md_path
    print(f"   ⚠  找不到图片: '{filename}'  ←  {rel}")
