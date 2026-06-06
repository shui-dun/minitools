# md2html

将 Markdown 笔记目录转换为 HTML 网站

## 功能

- **自动修复图片/笔记链接**——扫描笔记目录中所有图片/笔记文件，修复 Markdown 文件中的图片/笔记链接，同时支持wiki链接和md链接
- **目录忽略**——可配置需要跳过目录列表（如 `.git`、`.obsidian`），其下所有子目录中的 .md 文件均不会生成 HTML。
- **Docker + Nginx 部署**——自动生成 `nginx.conf`、`docker-compose.yml`，配合 `post-receive` hook 实现 push 即部署。

## 快速开始

### 1. 安装

```bash
cd md2html
uv tool install . --editable --reinstall
```

### 2. 配置

```bash
# 复制配置模板到家目录
cp config.template.toml ~/.md2html.toml
```

编辑 `~/.md2html.toml`

### 3. 服务器端（一次性设置）

```bash
md2html --setup-server
```

该命令会自动在服务器上创建 bare 仓库、工作目录、安装并配置好 post-receive hook。

### 4. 构建

```bash
md2html
```

以后笔记有更新，也只用运行这个命令就行

## 单测

```bash
uv run pytest tests/ -v
```