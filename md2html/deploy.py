"""
MkDocs 构建、部署文件生成、Git 操作。
"""

import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from mkdocs.commands.build import build
from mkdocs.config import load_config

from config_model import Config

# =============================================================================
# 模板
# =============================================================================

NGINX_CONF_TEMPLATE = """\
server {{
    listen       {nginx_port};

    root   /usr/share/nginx/html;
    index  index.html index.htm;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml
               application/xml application/xml+rss text/javascript image/svg+xml;
    gzip_min_length 256;

    # 静态资源缓存（mkdocs 生成的文件名带哈希，可以适当缓存）
    location /assets/ {{
        expires 1d;
        add_header Cache-Control "public, immutable";
    }}
}}
"""

DOCKER_COMPOSE_TEMPLATE = """\
version: "3.8"

services:
  notes:
    image: nginx:alpine
    ports:
      - "{docker_host_port}:{nginx_port}"
    volumes:
      - ./site:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
"""

POST_RECEIVE_TEMPLATE = """\
#!/bin/bash
set -e

WORK_TREE="{work_tree}"
GIT_DIR="{git_dir}"

if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DC="docker compose"
elif command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    echo "✖  未找到 docker compose 或 docker-compose 命令，请安装 Docker。"
    exit 1
fi

# Git 通过标准输入（stdin）向 post-receive 钩子传入每行三个值：
#   oldrev —— 推送前的旧 commit SHA
#   newrev —— 推送后的新 commit SHA
#   ref    —— 被推送的分支引用名，例如 refs/heads/master
# while 循环逐行读取，支持一次推送多个分支的情况
while read oldrev newrev ref; do
    if [ "$ref" = "refs/heads/master" ]; then
        echo ">>> 正在部署笔记网站 (ref: $ref, newrev: $newrev)..."

        git --work-tree="$WORK_TREE" --git-dir="$GIT_DIR" checkout -f

        cd "$WORK_TREE"
        $DC up -d

        echo ">>> 部署完成。"
    fi
done
"""


# =============================================================================
# 首页背景图片处理
# =============================================================================

def prepare_background(notes_dir: str, docs_dir: Path) -> str | None:
    """在笔记根目录查找 bg.jpg，找到则复制到 docs_dir/assets/ 并返回文件名。"""
    notes_root = Path(notes_dir)
    bg_path = notes_root / "bg.jpg"
    if bg_path.is_file():
        assets_dir = docs_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bg_path, assets_dir / "bg.jpg")
        print(f"   找到首页背景图: {bg_path}")
        return "bg.jpg"
    return None


def write_extra_css(docs_dir: Path, bg_filename: str | None) -> None:
    """在 docs_dir 下生成 stylesheets/extra.css。有背景图时使用图片，无背景图时留空。"""
    stylesheets_dir = docs_dir / "stylesheets"
    stylesheets_dir.mkdir(parents=True, exist_ok=True)

    if bg_filename:
        css_content = f"""\
/* 首页背景图片 */
body.homepage {{
    background-image: url('../assets/{bg_filename}');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}

/* 首页背景图片上的半透明内容区 */
body.homepage .md-main {{
    background: rgba(255, 255, 255, 0.7);
}}

body.homepage .md-sidebar {{
    background: rgba(255, 255, 255, 0.85);
}}
"""
    else:
        css_content = "/* 未配置首页背景图 */\n"

    (stylesheets_dir / "extra.css").write_text(css_content, encoding="utf-8")


def write_extra_js(docs_dir: Path) -> None:
    """在 docs_dir 下生成 javascripts/extra.js，用于在首页 <body> 上添加 homepage 类。"""
    js_dir = docs_dir / "javascripts"
    js_dir.mkdir(parents=True, exist_ok=True)

    js_content = """\
/* 检测当前页面是否为首页，是则给 body 添加 homepage 类 */
(function () {
    var path = window.location.pathname;
    var isHome = path === '/' || path.endsWith('/index.html') || path.endsWith('/');
    if (isHome) {
        document.body.classList.add('homepage');
    }
})();
"""
    (js_dir / "extra.js").write_text(js_content, encoding="utf-8")


# =============================================================================
# MkDocs 配置生成与构建
# =============================================================================


def generate_mkdocs_yml(cfg: Config, output_dir: Path) -> Path:
    """在 output_dir 中生成 mkdocs.yml。"""
    lines = [
        f"site_name: {cfg.site_name}",
        "",
        "use_directory_urls: false",
        "",
        "theme:",
        "  name: material",
        "  language: " + cfg.site_language,
        "  palette:",
        f"    scheme: {cfg.theme_palette}",
        "    primary: indigo",
        "    accent: indigo",
        "  features:",
        "    - navigation.instant",
        "    - navigation.tracking",
        "    - navigation.tabs",
        "    - navigation.sections",
        "    - navigation.indexes",
        "    - search.suggest",
        "    - search.highlight",
        "    - content.code.copy",
        "",
        "docs_dir: docs",
        f"site_dir: {output_dir / 'site'}",
        "",
        "extra_css:",
        "  - stylesheets/extra.css",
        "",
        "extra_javascript:",
        "  - javascripts/extra.js",
        "",
        "markdown_extensions:",
        "  - admonition",
        "  - pymdownx.highlight",
        "  - pymdownx.superfences",
        "  - pymdownx.tasklist:",
        "      custom_checkbox: true",
        "  - footnotes",
        "  - tables",
    ]

    yml_path = output_dir / "mkdocs.yml"
    yml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return yml_path


def run_mkdocs_build(yml_path: Path) -> None:
    """执行 mkdocs build。"""
    print(f"\n🔨 使用 MkDocs 构建网站 (配置: {yml_path})...")
    try:
        config = load_config(str(yml_path))
        config["plugins"].run_event("startup", command="build", dirty=False)
        try:
            build(config)
        finally:
            config["plugins"].run_event("shutdown")
    except Exception as exc:
        print(f"✖  mkdocs build 失败：{exc}")
        sys.exit(1)
    print("   网站构建完成。")


# =============================================================================
# 部署文件
# =============================================================================


def write_deployment_files(cfg: Config, output_dir: Path) -> None:
    """写入 nginx.conf、docker-compose.yml 到输出目录。"""
    nginx_conf = NGINX_CONF_TEMPLATE.format(nginx_port=cfg.nginx_port)
    (output_dir / "nginx.conf").write_text(nginx_conf, encoding="utf-8")

    compose = DOCKER_COMPOSE_TEMPLATE.format(
        docker_host_port=cfg.docker_host_port,
        nginx_port=cfg.nginx_port,
    )
    (output_dir / "docker-compose.yml").write_text(compose, encoding="utf-8")

    (output_dir / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.DS_Store\nThumbs.db\n", encoding="utf-8"
    )


# =============================================================================
# Git 操作
# =============================================================================


def ensure_git_repo(output_dir: Path) -> None:
    """如果输出目录不是 git 仓库，则初始化。"""
    if not (output_dir / ".git").is_dir():
        subprocess.run(["git", "-C", str(output_dir), "init"], check=True)
        print("   已初始化输出目录 git 仓库。")


def git_commit_and_push(output_dir: Path, server_remote: str) -> None:
    """提交变更并推送到服务器。"""
    subprocess.run(["git", "-C", str(output_dir), "add", "-A"], check=True)

    # 检查是否有变更
    result = subprocess.run(
        ["git", "-C", str(output_dir), "diff", "--cached", "--quiet"],
        capture_output=True,
    )
    if result.returncode == 0:
        print("   没有变更需要提交——网站已是最新。")
    else:
        subprocess.run(
            ["git", "-C", str(output_dir), "commit", "-m", f"site: 更新 {_timestamp()}"],
            check=True,
        )

    # 确保 remote 存在
    _ensure_remote(output_dir, server_remote)

    print(f"   推送到 {server_remote} ...")
    subprocess.run(
        ["git", "-C", str(output_dir), "push", "-u", "origin", "master"],
        check=True,
    )


def _ensure_remote(output_dir: Path, server_remote: str) -> None:
    """确保 origin remote 指向正确的服务器地址。"""
    remotes = subprocess.run(
        ["git", "-C", str(output_dir), "remote"],
        capture_output=True,
        text=True,
    ).stdout.strip()

    if "origin" not in remotes:
        subprocess.run(["git", "-C", str(output_dir), "remote", "add", "origin", server_remote], check=True)
    else:
        subprocess.run(["git", "-C", str(output_dir), "remote", "set-url", "origin", server_remote], check=True)


def _timestamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# =============================================================================
# 服务端一键部署（--setup-server）
# =============================================================================


def setup_server(cfg: Config) -> None:
    """通过 SSH 在服务器上一键完成 bare 仓库初始化、工作目录创建、
    post-receive hook 安装。"""
    server_remote = cfg.server_remote
    work_tree = cfg.server_work_tree

    # 校验必要配置
    if not server_remote:
        print("✖  未配置 server_remote，请在 ~/.md2html.toml 中设置服务器远程地址。")
        sys.exit(1)
    if not work_tree:
        print("✖  未配置 server_work_tree，请在 ~/.md2html.toml 中设置服务器工作目录。")
        sys.exit(1)

    # 解析 server_remote，提取 SSH 连接信息和 GIT_DIR
    parsed = urlparse(server_remote)

    if parsed.scheme not in ("ssh", ""):
        print(f"✖  server_remote 协议不支持: {parsed.scheme}，仅支持 ssh:// 格式。")
        print(f"   当前值: {server_remote}")
        sys.exit(1)

    git_dir = parsed.path
    if not git_dir:
        print(f"✖  无法从 server_remote 解析出服务器端路径: {server_remote}")
        sys.exit(1)

    # 构建 SSH 目标地址
    if parsed.username:
        ssh_target = f"{parsed.username}@{parsed.hostname}"
    else:
        ssh_target = parsed.hostname

    if parsed.port:
        ssh_target = f"{ssh_target}"
        ssh_port_args = ["-p", str(parsed.port)]
    else:
        ssh_port_args = []

    print(f"\n🚀 开始在服务器 {ssh_target} 上部署...")
    print(f"   Git 仓库: {git_dir}")
    print(f"   工作目录: {work_tree}")

    # 生成 post-receive hook 脚本
    hook_script = POST_RECEIVE_TEMPLATE.format(
        work_tree=work_tree,
        git_dir=git_dir,
    )

    # 组装服务器端命令
    shell_cmd = (
        f"set -e;"
        f"echo '>>> 创建 bare 仓库...';"
        f"if [ ! -d {git_dir} ]; then"
        f"  mkdir -p $(dirname {git_dir});"
        f"  git init --bare {git_dir};"
        f"else"
        f"  echo '    (已存在，跳过)';"
        f"fi;"
        f"echo '>>> 创建工作目录...';"
        f"mkdir -p {work_tree};"
        f"echo '>>> 安装 post-receive hook...';"
        f"cat > {git_dir}/hooks/post-receive << 'ENDOFHOOK'\n"
        f"{hook_script}\n"
        f"ENDOFHOOK\n"
        f"chmod +x {git_dir}/hooks/post-receive;"
        f"echo '';"
        f"echo '>>> 检查 Docker 是否安装...';"
        f"if command -v docker &> /dev/null; then"
        f"  echo '    Docker 已安装 ✅';"
        f"else"
        f"  echo '    ⚠ Docker 未安装，请在服务器上安装 Docker 后再推送部署。';"
        f"fi;"
        f"echo '';"
        f"echo '✅ 服务端设置完成。';"
    )

    ssh_args = ["ssh", *ssh_port_args, ssh_target, shell_cmd]

    try:
        subprocess.run(ssh_args, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"\n✖  SSH 执行失败（退出码 {exc.returncode}），请检查服务器连接。")
        sys.exit(1)
    except FileNotFoundError:
        print("\n✖  未找到 ssh 命令，请确认已安装 OpenSSH 客户端。")
        sys.exit(1)
