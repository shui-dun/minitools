"""CLI 入口。

串接整个解读 pipeline：
  convert → read → split → interpret → write

用法：
  bookwhisper interpret book.epub
  bookwhisper interpret book.mobi --output ./output --chunk.max-chars 2000
  bookwhisper interpret book.epub --config config.yaml
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from bookwhisper import __version__
from bookwhisper.checkpoint import ChapterResult, CheckpointManager
from bookwhisper.config import AppConfig, load_config
from bookwhisper.converter import FormatConverter
from bookwhisper.epub_processor import EpubReader, EpubWriter
from bookwhisper.interpreter import DeepSeekInterpreter, InterpretError
from bookwhisper.splitter import ChapterSplitter, Section

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bookwhisper")


def _build_cli_overrides(
    deepseek_model: str | None,
    deepseek_base_url: str | None,
    deepseek_temperature: float | None,
    chunk_max_chars: int | None,
    chunk_book_summary_chars: int | None,
    output_dir: str | None,
    output_suffix: str | None,
    max_retries: int | None,
    resume_flag: bool | None,
) -> dict[str, str]:
    """将 CLI 参数转换为点号路径的覆盖字典。"""
    overrides: dict[str, str] = {}

    if deepseek_model is not None:
        overrides["deepseek.model"] = deepseek_model
    if deepseek_base_url is not None:
        overrides["deepseek.base_url"] = deepseek_base_url
    if deepseek_temperature is not None:
        overrides["deepseek.temperature"] = str(deepseek_temperature)
    if chunk_max_chars is not None:
        overrides["chunk.max_chars"] = str(chunk_max_chars)
    if chunk_book_summary_chars is not None:
        overrides["chunk.book_summary_chars"] = str(chunk_book_summary_chars)
    if output_dir is not None:
        overrides["output.dir"] = output_dir
    if output_suffix is not None:
        overrides["output.suffix"] = output_suffix
    if max_retries is not None:
        overrides["max_retries"] = str(max_retries)
    if resume_flag is not None:
        overrides["resume"] = str(resume_flag)

    return overrides


def _parse_chapter_index(chapter_id: str) -> int:
    """从 section ID 中提取章节序号。

    "chapter_000" → 0
    "chapter_002_section_0" → 2
    """
    parts = chapter_id.split("_")
    return int(parts[1])


# ============================== CLI ==============================


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """bookWhisper — AI 解读书籍，输出口语化 EPUB，可导入微信读书朗读。"""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    default=None,
    help="YAML 配置文件路径。",
)
@click.option(
    "--output", "-o",
    default=None,
    help="输出目录。",
)
@click.option(
    "--output-suffix",
    default=None,
    help="输出 EPUB 文件名后缀（默认: _interpreted）。",
)
@click.option(
    "--deepseek-model",
    default=None,
    help="DeepSeek 模型名（默认: deepseek-v4-pro）。",
)
@click.option(
    "--deepseek-base-url",
    default=None,
    help="DeepSeek API 地址。",
)
@click.option(
    "--deepseek-temperature",
    type=float,
    default=None,
    help="温度参数（默认: 0.3）。",
)
@click.option(
    "--chunk-max-chars",
    type=int,
    default=None,
    help="单块最大字符数（默认: 15000）。",
)
@click.option(
    "--chunk-book-summary-chars",
    type=int,
    default=None,
    help="整书摘要最大字数（默认: 800）。",
)
@click.option(
    "--max-retries",
    type=int,
    default=None,
    help="API 调用最大重试次数（默认: 3）。",
)
@click.option(
    "--resume/--no-resume",
    default=None,
    help="是否从断点续传（默认: 启用）。",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="详细日志输出。",
)
def interpret(
    input_file: str,
    config: str | None,
    output: str | None,
    output_suffix: str | None,
    deepseek_model: str | None,
    deepseek_base_url: str | None,
    deepseek_temperature: float | None,
    chunk_max_chars: int | None,
    chunk_book_summary_chars: int | None,
    max_retries: int | None,
    resume: bool | None,
    verbose: bool,
) -> None:
    """解读书籍并输出 EPUB。

    INPUT_FILE: 输入文件路径（支持 .epub / .mobi / .azw3）。
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # ---- 加载配置 ----
    app_config = load_config(config)
    cli_overrides = _build_cli_overrides(
        deepseek_model=deepseek_model,
        deepseek_base_url=deepseek_base_url,
        deepseek_temperature=deepseek_temperature,
        chunk_max_chars=chunk_max_chars,
        chunk_book_summary_chars=chunk_book_summary_chars,
        output_dir=output,
        output_suffix=output_suffix,
        max_retries=max_retries,
        resume_flag=resume,
    )
    app_config.apply_cli_overrides(cli_overrides)

    # 校验 API Key
    if not app_config.deepseek.api_key:
        click.echo(
            "错误：未设置 DeepSeek API Key。\n"
            "请通过以下方式之一设置：\n"
            "  1. 环境变量: export DEEPSEEK_API_KEY=sk-xxx\n"
            "  2. 配置文件: 在 YAML 中设置 deepseek.api_key\n"
            "  3. 命令行: 不支持（安全原因），请使用前两种方式",
            err=True,
        )
        sys.exit(1)

    input_path = Path(input_file).resolve()
    output_dir = Path(app_config.output.dir).resolve()

    click.echo("=" * 60)
    click.echo(f"  bookWhisper v{__version__}")
    click.echo(f"  输入: {input_path}")
    click.echo(f"  输出: {output_dir}")
    click.echo(f"  模型: {app_config.deepseek.model}")
    click.echo("=" * 60)

    # ========== Pipeline ==========

    try:
        _run_pipeline(input_path, output_dir, app_config)
    except InterpretError as e:
        click.echo(f"\n解读失败: {e.message}", err=True)
        click.echo("你可以重新运行此命令从断点恢复（默认启用 --resume）。", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n发生未预期的错误: {e}", err=True)
        if verbose:
            raise
        sys.exit(1)


def _run_pipeline(
    input_path: Path,
    output_dir: Path,
    config: AppConfig,
) -> None:
    """执行完整的解读 pipeline。"""

    # Step 1: 格式转换 → 统一为 EPUB
    click.echo("\n[1/6] 格式转换...")
    converter = FormatConverter()
    epub_path = converter.convert(input_path)

    # Step 2: 读取 EPUB
    click.echo("\n[2/6] 解析 EPUB...")
    reader = EpubReader(epub_path)
    click.echo(f"  书名: {reader.title}")
    click.echo(f"  章节数: {len(reader.chapters)}")
    click.echo(f"  总字符数: {reader.total_chars:,}")

    if not reader.chapters:
        click.echo("错误：未能从 EPUB 中提取到任何章节内容。", err=True)
        sys.exit(1)

    # Step 3: 初始化断点续传
    click.echo("\n[3/6] 检查断点续传...")
    checkpoint = CheckpointManager(output_dir, epub_path)
    checkpoint.set_total_chapters(len(reader.chapters))

    if config.resume and checkpoint.all_done:
        click.echo("  所有章节已完成解读，如需重新解读请使用 --no-resume。")
        # 仍然重新生成 EPUB（用户可能改了配置）
        _rebuild_epub(reader, checkpoint, output_dir, config)
        return

    if config.resume:
        done, total = checkpoint.progress
        if done > 0:
            click.echo(f"  断点续传: {done}/{total} 章已完成，从未完成处继续。")
        else:
            click.echo("  全新解读。")
    else:
        click.echo("  断点续传已禁用（--no-resume），将重新解读所有章节。")

    # Step 4: 分块
    click.echo("\n[4/6] 文本分块...")
    splitter = ChapterSplitter(max_chars=config.chunk.max_chars)
    sections = splitter.split_chapters(reader.chapters)
    click.echo(f"  共 {len(reader.chapters)} 章，切分为 {len(sections)} 个处理块。")

    # Step 5: 生成整书摘要
    click.echo("\n[5/6] 初始化 DeepSeek 解读器...")
    interpreter = DeepSeekInterpreter(config, checkpoint)

    # 尝试从 checkpoint 恢复摘要
    summary = checkpoint.get_book_summary()
    if summary:
        click.echo(f"  从 checkpoint 恢复整书摘要（{len(summary)} 字）。")
    else:
        click.echo("  正在生成整书摘要...")
        front_matter = reader.get_front_matter_text(config.chunk.book_summary_chars * 3)
        # 把书名显式传入，避免 AI 从正文中猜错书名
        front_matter = f"书名：《{reader.title}》\n\n{front_matter}"
        summary = interpreter.generate_summary(front_matter)
        click.echo(f"  整书摘要（{len(summary)} 字）已生成。")

    # Step 6: 逐块解读
    click.echo(f"\n[6/6] 开始解读（共 {len(sections)} 块）...\n")

    from tqdm import tqdm

    all_results: dict[int, list[ChapterResult]] = {}
    success_count = 0
    skip_count = 0

    # 跟踪上一块原文，用于同章内上下文传递
    prev_chapter_index = -1
    prev_section_text = ""

    pbar = tqdm(sections, desc="解读进度", unit="块")
    for section in pbar:
        section_id = section.id

        # 构建前文上下文（仅同章内传递，跨章重置）
        if section.chapter_index == prev_chapter_index and prev_section_text:
            # 取上一块原文末尾 1000 字，保持连贯性
            tail_len = min(len(prev_section_text), 1000)
            previous_context = prev_section_text[-tail_len:]
        else:
            previous_context = ""

        # 检查是否已完成
        if config.resume and checkpoint.is_done(section_id):
            # 从 checkpoint 恢复已解读的文本
            cached = checkpoint.get_result(section_id)
            if cached is not None:
                ch_idx = section.chapter_index
                if ch_idx not in all_results:
                    all_results[ch_idx] = []
                all_results[ch_idx].append(cached)
            skip_count += 1
            # 即使跳过，也要更新上下文跟踪，保证后续块的连贯性
            prev_chapter_index = section.chapter_index
            prev_section_text = section.text
            pbar.set_postfix({"跳过": skip_count, "完成": success_count})
            continue

        # 解读（带重试）
        try:
            result = interpreter.interpret_section_with_retry(
                section,
                summary,
                max_retries=config.max_retries,
                previous_text=previous_context,
            )
        except InterpretError as e:
            click.echo(f"\n解读失败: {section_id}: {e.message}", err=True)
            click.echo("你可以重新运行此命令从断点恢复。", err=True)
            sys.exit(1)

        # 收集结果
        ch_idx = section.chapter_index
        if ch_idx not in all_results:
            all_results[ch_idx] = []
        all_results[ch_idx].append(result)
        success_count += 1

        # 更新上下文跟踪
        prev_chapter_index = section.chapter_index
        prev_section_text = section.text

        pbar.set_postfix({"跳过": skip_count, "完成": success_count})

    pbar.close()

    click.echo(f"\n解读完成: 成功 {success_count} 块, 跳过 {skip_count} 块。")

    # 合并同章节的多块结果
    chapter_results: dict[int, str] = {}
    for ch_idx, results in sorted(all_results.items()):
        merged = "\n\n".join(r.interpreted_text for r in sorted(results, key=lambda r: r.chapter_id))
        chapter_results[ch_idx] = merged

    # Step 7: 写回 EPUB
    _rebuild_epub(reader, checkpoint, output_dir, config, chapter_results)


def _rebuild_epub(
    reader: EpubReader,
    checkpoint: CheckpointManager,
    output_dir: Path,
    config: AppConfig,
    chapter_results: dict[int, str] | None = None,
) -> None:
    """重建 EPUB（从 checkpoint 恢复场景，或解读完成后）。"""
    click.echo("\n正在生成 EPUB...")

    if chapter_results is None:
        # 从 checkpoint 恢复完整解读结果
        all_saved = checkpoint.get_all_results()
        if not all_saved:
            click.echo("  警告：checkpoint 中未保存完整解读文本，无法重建 EPUB。")
            click.echo("  请重新运行解读（使用 --no-resume 可强制重新解读所有章节）。")
            return

        # 按章节序号合并多段结果
        chapter_results = {}
        for ch_id, result in sorted(all_saved.items()):
            ch_idx = _parse_chapter_index(ch_id)
            if ch_idx not in chapter_results:
                chapter_results[ch_idx] = []
            chapter_results[ch_idx].append(result)

        # 合并同章节的多段文本
        merged_results: dict[int, str] = {}
        for ch_idx, results in sorted(chapter_results.items()):
            merged = "\n\n".join(
                r.interpreted_text for r in sorted(results, key=lambda r: r.chapter_id)
            )
            merged_results[ch_idx] = merged

        chapter_results = merged_results
        click.echo(f"  从 checkpoint 恢复了 {len(chapter_results)} 个章节的解读文本。")

    book_stem = Path(reader._path).stem  # type: ignore[attr-defined]
    output_name = f"{book_stem}{config.output.suffix}.epub"

    writer = EpubWriter(reader.book, reader.chapters)
    output_path = writer.write(
        output_dir / output_name,
        chapter_results,
        title_suffix=config.output.suffix.replace("_", "").replace("-", ""),
    )

    click.echo(f"\n✓ 输出 EPUB: {output_path}")
    click.echo("  你可以将此 EPUB 导入微信读书进行朗读。")


if __name__ == "__main__":
    cli()
