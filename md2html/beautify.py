import shutil
from pathlib import Path

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

/* 首页桌面端隐藏左右导航栏（手机端保留汉堡菜单） */
@media screen and (min-width: 76.25em) {{
    body.homepage .md-sidebar--primary {{
        display: none;
    }}

    body.homepage .md-sidebar--secondary {{
        display: none;
    }}
}}
"""
    else:
        css_content = "/* 未配置首页背景图 */\n\n"

    # grid cards 卡片样式（白色圆角 + 悬停浮起）
    css_content += """\
/* 首页卡片网格：白色圆角卡片，悬停浮起 */
.md-typeset .grid.cards > ul > li,
.md-typeset .grid.cards > ol > li {
    display: block;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    padding: 1.2rem;
    cursor: pointer;
    transition: box-shadow 0.2s, transform 0.15s;
}

.md-typeset .grid.cards > ul > li:hover,
.md-typeset .grid.cards > ol > li:hover {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}
"""

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

    /* 让首页 grid cards 整卡可点击 */
    document.addEventListener('DOMContentLoaded', function () {
        var cards = document.querySelectorAll('.grid.cards li');
        cards.forEach(function (card) {
            var link = card.querySelector('a');
            if (!link) return;
            card.addEventListener('click', function (e) {
                // 如果用户正在选中文字，不跳转
                var sel = window.getSelection();
                if (sel && sel.toString().length > 0) return;
                // 如果点击的是卡片内的其他链接，不拦截
                if (e.target.closest('a') && e.target.closest('a') !== link) return;
                link.click();
            });
        });
    });
})();
"""
    (js_dir / "extra.js").write_text(js_content, encoding="utf-8")
