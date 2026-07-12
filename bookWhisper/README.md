# bookWhisper

AI 解读书籍

## 解决的问题

直接读书（或听书）有几个痛点：

| 痛点 | bookWhisper 的解法 |
|------|-------------------|
| 书面语晦涩，听不太懂 | LLM 改写为口语短句 |
| 括号中的外文/注释打断节奏 | 融入正文，不照念括号 |
| 作者啰嗦，绕来绕去 | 识别核心论点，删除重复论证 |
| 学术黑话堆砌，听不懂 | 用例子和类比解释抽象概念 |
| 翻译腔（长句、被动态、"的的的"） | 改为地道中文短句 |
| TTS 在术语中间断错句 | 在术语前后自然断句 |
| 术语听不懂，不知道每个字怎么写 | 首次出现时逐字说明 + 白话解释 |
| 读起来枯燥，没动力 | 加入设问、类比、点评式过渡，像朋友聊天 |

---

## 整体流程

```
EPUB / MOBI / AZW3
        │
        ▼
  MOBI/AZW3 → Calibre CLI → EPUB（统一格式）
        │
        ▼
  ebooklib 解析 → 提取章节结构 + 正文
        │
        ▼
  DeepSeek 生成整书摘要（来自目录 + 前言）
        │
        ▼
  逐章发给 DeepSeek 解读（每章附带整书摘要作为上下文）
        │
        ▼
  解读后的文本替换原 EPUB 各章节内容
        │
        ▼
  输出新 EPUB（保留原书目录、插图、封面）
        │
        ▼
  导入微信读书 → 微信读书 TTS 朗读
```

---

## 安装

### 依赖

- **Python ≥ 3.10**
- **uv**（Python 包管理工具）
- **Calibre**（可选，仅处理 MOBI/AZW3 时需要）→ [下载](https://calibre-ebook.com/download)

### 安装步骤

```bash
# 克隆项目
git clone <repo-url> && cd bookWhisper

# 安装
uv tool install . --editable --reinstall
```

安装完成后，`bookwhisper` 命令即可在终端中全局使用。

### 设置 API Key

```bash
export DEEPSEEK_API_KEY=sk-你的key
```

---

## 快速开始

```bash
# 最基本的用法
bookwhisper interpret 经济学原理.epub

# 输出文件: ./output/经济学原理_interpreted.epub
```

把输出 EPUB 导入微信读书，就可以用微信读书的自然语音朗读了。

---

## 命令详解

### `bookwhisper interpret` — 解读一本书

```bash
bookwhisper interpret <输入文件> [选项]
```

#### 参数

| 参数 | 说明 |
|------|------|
| `INPUT_FILE` | 输入文件路径，支持 `.epub` / `.mobi` / `.azw3` |

#### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-c, --config PATH` | YAML 配置文件路径 | 无 |
| `-o, --output TEXT` | 输出目录 | `./output` |
| `--output-suffix TEXT` | 输出文件名后缀 | `_interpreted` |
| `--deepseek-model TEXT` | DeepSeek 模型名 | `deepseek-v4-pro` |
| `--deepseek-base-url TEXT` | API 地址 | `https://api.deepseek.com` |
| `--deepseek-temperature FLOAT` | 温度参数（0-1） | `0.3` |
| `--chunk-max-chars INTEGER` | 单块最大字符数 | `3000` |
| `--chunk-book-summary-chars INTEGER` | 整书摘要最大字数 | `500` |
| `--max-retries INTEGER` | API 失败最大重试次数 | `3` |
| `--resume / --no-resume` | 是否断点续传 | 启用 |
| `-v, --verbose` | 详细日志 | 关闭 |

#### 使用示例

```bash
# 解读 EPUB，输出到指定目录
bookwhisper interpret 社会学导论.epub --output ./audiobooks

# 解读 MOBI 文件（需要安装 Calibre）
bookwhisper interpret 认知觉醒.mobi

# 调小块大小，降低单次 API 调用量
bookwhisper interpret 大部头.epub --chunk-max-chars 1500

# 强制重新解读整本书（忽略断点续传）
bookwhisper interpret 已读过的书.epub --no-resume

# 使用 reasoning 模型
bookwhisper interpret 哲学书.epub --deepseek-model deepseek-reasoner

# 开启详细日志排查问题
bookwhisper interpret 问题书.epub --verbose

# 组合使用：通过配置文件 + CLI 覆盖部分参数
bookwhisper interpret 书籍.epub --config my_config.yaml --chunk-max-chars 2000
```

---

## 配置文件

程序会自动加载家目录下的 `~/.bookwhisper.yaml`。项目里提供了模板文件，复制到 home 目录后按需修改即可：

```bash
# 首次使用：从项目模板复制到家目录
cp config.template.yaml ~/.bookwhisper.yaml

# 编辑配置（修改 model、输出目录等）
vim ~/.bookwhisper.yaml
```

模板内容（`config.template.yaml`）：

```yaml
deepseek:
  api_key: "${DEEPSEEK_API_KEY}"  # 支持环境变量
  model: "deepseek-v4-pro"
  base_url: "https://api.deepseek.com"
  temperature: 0.3

chunk:
  max_chars: 3000               # 单块最大中文字符数
  book_summary_chars: 500        # 整书摘要最大字数

output:
  dir: "./output"
  suffix: "_interpreted"
```

有了家目录配置后，直接运行即可，不需要每次指定 `--config`：

```bash
# 自动加载 ~/.bookwhisper.yaml
bookwhisper interpret 书籍.epub
```

如果需要临时使用另一份配置，也可以通过 `--config` 覆盖：

```bash
bookwhisper interpret 书籍.epub --config other_config.yaml
```

**配置优先级**：CLI 参数 > 环境变量 > 配置文件（`--config` 指定 > `~/.bookwhisper.yaml`） > 默认值

---

## 断点续传

解读一本几十章的书可能需要半小时以上。如果网络波动导致中断，重新运行相同命令即可从断点继续——已完成的章节不会重复调用 API。

```bash
# 第一次运行，跑到第 18 章时网络断了
bookwhisper interpret 长书.epub

# 重新运行，自动跳过前 17 章，从第 18 章继续
bookwhisper interpret 长书.epub
```

断点信息保存在输出目录下的 `.bookwhisper_checkpoint.json` 文件中。

```bash
# 强制从头重新解读
bookwhisper interpret 长书.epub --no-resume
```

---

## 输入 vs 输出示例

### 原文（典型学术写作）

> 值得注意的是，在相当多的学术话语场域中，哈贝马斯所提出的"交往理性"（kommunikative Rationalität）这一概念，在某种意义上可以被视为是对韦伯目的理性（Zweckrationalität）批判性重构的理论尝试。

### 解读后（适合听读）

> 这里要提到一个重要的概念：交往理性。交，交流的交；往，来往的往；理，道理的理；性，性质的性。交往理性是哲学家哈贝马斯提出的。你可以这样理解：人和人通过对话达成共识的那种理性，就叫交往理性。
>
> 哈贝马斯为什么要提出这个概念呢？其实他是在回应另一位大思想家韦伯。韦伯说，现代人做事太算计了，做什么都讲效率和目的——这叫目的理性。哈贝马斯说，不对，人跟人沟通不只是为了达成目的，还有互相理解的层面。所以交往理性，就是他对韦伯观点的一个修正。

注意解读后的文本是如何：
- 逐字拆解术语 → "交，交流的交；往，来往的往…"
- 用大白话解释 → "人和人通过对话达成共识的那种理性"
- 背景故事化 → "其实他是在回应另一位大思想家"
- 口语设问 → "哈贝马斯为什么要提出这个概念呢？"

---

## 输入格式支持

| 格式 | 处理方式 | 额外依赖 |
|------|---------|---------|
| EPUB | 直接处理 | 无 |
| MOBI | Calibre CLI 转为 EPUB 后处理 | [Calibre](https://calibre-ebook.com/download) |
| AZW3 | Calibre CLI 转为 EPUB 后处理 | [Calibre](https://calibre-ebook.com/download) |

> 首次处理 MOBI/AZW3 时，程序会自动检测 Calibre 是否安装。如果未安装，会给出安装指引。

---

## 运行测试

```bash
uv run pytest tests/ -v
```

70 个测试覆盖了所有模块：配置加载、格式转换、EPUB 读写、文本分块、API 调用（mock）、重试逻辑、断点续传、CLI 集成。
