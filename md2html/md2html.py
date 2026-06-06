import shutil
import sys
from pathlib import Path
import tomllib

from config_model import Config
from image_processor import build_image_table
from wikilink_processor import build_note_table
from processor import process_markdown_files, copy_used_images
from deploy import (
    generate_mkdocs_yml,
    run_mkdocs_build,
    write_deployment_files,
    ensure_git_repo,
    git_commit_and_push,
    setup_server,
    prepare_background,
    write_extra_css,
    write_extra_js,
)


# =============================================================================
# 配置加载
# =============================================================================


def load_config() -> Config:
    """从 ~/.md2html.toml 加载配置并校验，返回 Config 值对象。"""
    config_path = Path.home() / ".md2html.toml"

    if not config_path.exists():
        print(f"✖  配置文件不存在: {config_path}")
        print("   请将 config.template.toml 复制到 ~/.md2html.toml 并修改。")
        sys.exit(1)

    try:
        with open(config_path, "rb") as fh:
            raw = tomllib.load(fh)
    except Exception as exc:
        print(f"✖  解析配置文件失败 {config_path}: {exc}")
        sys.exit(1)

    # 所有配置项强制从文件读取，不提供默认值，确保行为完全由配置文件控制
    required_keys = [
        "notes_dir",
        "output_dir",
        "site_name",
        "site_language",
        "theme_palette",
        "nginx_port",
        "docker_host_port",
    ]
    missing = [k for k in required_keys if k not in raw]
    if missing:
        print(f"✖  配置文件缺少必填项: {', '.join(missing)}")
        print("   请参考 config.template.toml 补全所有配置项。")
        sys.exit(1)

    notes_dir = raw["notes_dir"]
    if not Path(notes_dir).is_dir():
        print(f"✖  notes_dir 不存在或不是目录: {notes_dir}")
        sys.exit(1)

    # 路径转换：字典无法自动完成，需要手动处理
    raw["notes_dir"] = str(Path(notes_dir).resolve())

    # 可选配置项补充默认值
    raw.setdefault("ignore_dirs", [])
    raw.setdefault("server_remote", "")
    raw.setdefault("server_work_tree", "")

    return Config(**raw)


# =============================================================================
# 主流程
# =============================================================================


def build_site(cfg: Config) -> None:
    """核心流程：处理笔记 → 构建网站 → 写入部署文件 → 推送。"""
    notes_dir = cfg.notes_dir
    output_dir = Path(cfg.output_dir)
    ignore_dirs = cfg.ignore_dirs

    # 第一步：扫描图片和笔记，构建哈希表
    print("\n📸 扫描资源文件 ...")
    image_table = build_image_table(notes_dir, ignore_dirs)
    print(f"   找到 {len(image_table)} 个图片文件。")
    note_table = build_note_table(notes_dir, ignore_dirs)
    print(f"   找到 {len(note_table)} 个笔记文件。")

    # 第二步：准备临时 docs 目录，复制并修复 Markdown
    docs_dir = output_dir / "docs"
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(parents=True)

    print("\n📝 处理 Markdown 文件 ...")
    used_images = process_markdown_files(notes_dir, docs_dir, image_table, note_table, ignore_dirs)

    # 第三步：复制被引用的图片
    copy_used_images(image_table, used_images, docs_dir / "assets")

    # 第三步半：首页背景图片处理
    bg_filename = prepare_background(notes_dir, docs_dir)
    write_extra_css(docs_dir, bg_filename)
    write_extra_js(docs_dir)

    # 第四步：生成 mkdocs.yml 并构建
    yml_path = generate_mkdocs_yml(cfg, output_dir)
    run_mkdocs_build(yml_path)

    # 第五步：写入部署文件
    print("\n📦 写入部署文件 ...")
    write_deployment_files(cfg, output_dir)

    # 第六步：Git 提交与推送
    ensure_git_repo(output_dir)
    server_remote = cfg.server_remote
    if server_remote:
        git_commit_and_push(output_dir, server_remote)
    else:
        print(f"\n💡 提示: 在 ~/.md2html.toml 中配置 'server_remote' 即可自动推送。")


def main() -> None:
    cfg = load_config()

    if "--setup-server" in sys.argv:
        setup_server(cfg)
        return

    build_site(cfg)
    print("\n✅ 完成——网站已生成。")


if __name__ == "__main__":
    main()
