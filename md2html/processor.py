"""
处理 Markdown 文件的编排层：协调图片处理和 wikilink 处理。
"""

import os
import shutil
from pathlib import Path

from image_processor import fix_image_links
from wikilink_processor import fix_wikilinks


# =============================================================================
# Markdown 文件批量处理
# =============================================================================


def process_markdown_files(
    notes_dir: str,
    docs_dir: Path,
    image_table: dict[str, str],
    note_table: dict[str, Path],
    ignore_dirs: list[str],
) -> set[str]:
    """复制笔记目录中所有 .md 文件到 docs_dir（保持相对目录结构），修复图片链接和 wikilink，返回被引用图片的文件名集合。
    """
    notes_path = Path(notes_dir)

    # 图片最终统一放到 docs_dir/assets/ 下
    assets_dir = docs_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # === 遍历笔记目录下所有 .md 文件 ===
    used_images: set[str] = set()
    md_count = 0

    for root, dirs, files in os.walk(notes_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        files[:] = [f for f in files if f not in ignore_dirs]

        for fname in files:
            if not fname.endswith(".md"):
                continue

            src = Path(root) / fname

            # rel: Path.relative_to() 从绝对路径中"减掉"基础路径，得到相对部分
            #     比如 C:\note\技术\教程.md 减掉 C:\note → 技术\教程.md
            rel = src.relative_to(notes_path)

            # dst: 输出根目录拼上相对路径，保持原有的子目录结构
            dst = docs_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)

            # --- 复制文件 + 修复图片链接 + 修复 wikilink ---
            shutil.copy2(src, dst)
            fix_image_links(dst, image_table, used_images)
            fix_wikilinks(dst, note_table, rel)
            md_count += 1

    print(f"   已处理 {md_count} 个 Markdown 文件")
    return used_images


def copy_used_images(image_table: dict[str, str], used_images: set[str], assets_dir: Path) -> None:
    """将被引用的图片复制到 assets 目录。"""
    print(f"\n🖼   复制 {len(used_images)} 个被引用的图片到 {assets_dir} ...")
    assets_dir.mkdir(parents=True, exist_ok=True)
    for fname in used_images:
        shutil.copy2(image_table[fname], assets_dir / fname)
