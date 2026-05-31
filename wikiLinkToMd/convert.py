"""
将 Obsidian 风格的 ![[Pasted image xxx.png]] 和 ![[Pasted image xxx.png|size]]
转换为标准 Markdown 的 ![](url_encoded_path) 格式。

用法:
    uv run convert.py <目标目录>

示例:
    uv run convert.py C:/Users/shuidun/Desktop/note
"""

import re
import sys
from pathlib import Path

# 匹配 ![[<文件名>]] 或 ![[<文件名>|<别名/尺寸>]]
PATTERN = re.compile(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def convert_link(match: re.Match) -> str:
    """将匹配到的 Obsidian 链接转换为标准 Markdown 图片链接，空格转 %20。"""
    filename = match.group(1)  # e.g. "Pasted image 20241204120043.png"
    encoded = filename.replace(" ", "%20")
    return f"![]({encoded})"


def process_file(filepath: Path) -> int:
    """处理单个 md 文件，返回替换次数。"""
    content = filepath.read_text(encoding="utf-8")
    new_content, count = PATTERN.subn(convert_link, content)
    if count > 0:
        filepath.write_text(new_content, encoding="utf-8")
    return count


def main(target_dir: str) -> None:
    root = Path(target_dir)
    if not root.is_dir():
        print(f"错误: 目录不存在 — {target_dir}")
        sys.exit(1)

    md_files = list(root.rglob("*.md"))
    print(f"找到 {len(md_files)} 个 .md 文件")

    total_replacements = 0
    files_changed = 0

    for f in md_files:
        n = process_file(f)
        if n > 0:
            total_replacements += n
            files_changed += 1

    print(f"完成: 修改了 {files_changed} 个文件，共 {total_replacements} 处替换。")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: uv run convert.py <目标目录>")
        sys.exit(1)
    main(sys.argv[1])
