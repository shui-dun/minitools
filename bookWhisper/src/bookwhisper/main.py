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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click
from click_default_group import DefaultGroup

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
    parallel_workers: int | None,
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
    if parallel_workers is not None:
        overrides["parallel_workers"] = str(parallel_workers)

    return overrides


def _parse_chapter_index(chapter_id: str) -> int:
    """从 section ID 中提取章节序号。

    "chapter_000" → 0
    "chapter_002_section_0" → 2
    """
    parts = chapter_id.split("_")
    return int(parts[1])


# ============================== CLI ==============================


@click.group(cls=DefaultGroup, default="interpret")
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
@click.option(
    "--parallel-workers",
    type=int,
    default=None,
    help="并行解读 worker 数量（默认: 5）。",
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
    parallel_workers: int | None,
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
        parallel_workers=parallel_workers,
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

    if config.resume:
        done, total = checkpoint.progress
        if done > 0:
            click.echo(f"  断点续传: {done}/{total} 块已完成，从未完成处继续。")
        else:
            click.echo("  全新解读。")
    else:
        click.echo("  断点续传已禁用（--no-resume），将重新解读所有章节。")

    # Step 4: 分块
    click.echo("\n[4/6] 文本分块...")
    splitter = ChapterSplitter(max_chars=config.chunk.max_chars)
    sections = splitter.split_chapters(reader.chapters)
    checkpoint.set_total_sections(len(sections))
    click.echo(f"  共 {len(reader.chapters)} 章，切分为 {len(sections)} 个处理块。")

    # 在得知实际节段数后，重新检查是否全部完成
    if config.resume and checkpoint.all_done:
        click.echo("  所有章节已完成解读，如需重新解读请使用 --no-resume。")
        _rebuild_epub(reader, checkpoint, output_dir, config)
        return

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

    # Step 6: 按章节并行解读
    # 将 sections 按章节分组，同章内保持顺序（需要上下文传递），跨章并行
    chapter_sections: dict[int, list[Section]] = {}
    for s in sections:
        chapter_sections.setdefault(s.chapter_index, []).append(s)

    num_workers = max(1, config.parallel_workers)
    click.echo(f"\n[6/6] 开始并行解读（共 {len(sections)} 块，{len(chapter_sections)} 章，{num_workers} worker）...\n")

    from tqdm import tqdm

    all_results: dict[int, list[ChapterResult]] = {}
    counters = {"success": 0, "skip": 0}
    counter_lock = threading.Lock()
    error_event = threading.Event()
    first_error: Exception | None = None

    pbar = tqdm(total=len(sections), desc="解读进度", unit="块")

    def update_progress(skipped: bool = False) -> None:
        with counter_lock:
            if skipped:
                counters["skip"] += 1
            else:
                counters["success"] += 1
            pbar.set_postfix({"跳过": counters["skip"], "完成": counters["success"]})
        pbar.update(1)

    def process_chapter(ch_idx: int, chap_sections: list[Section]) -> list[ChapterResult] | None:
        """处理单章内所有块（顺序执行，保持上下文传递）。"""
        nonlocal first_error

        try:
            results: list[ChapterResult] = []
            prev_text = ""

            for section in chap_sections:
                if error_event.is_set():
                    return None

                # 检查缓存
                if config.resume and checkpoint.is_done(section.id):
                    cached = checkpoint.get_result(section.id)
                    if cached is not None:
                        results.append(cached)
                        prev_text = cached.interpreted_text
                    update_progress(skipped=True)
                    continue

                # 解读（带重试）
                result = interpreter.interpret_section(
                    section, summary, previous_text=prev_text,
                )

                # 二次全文重写
                refined_text = interpreter.review_and_refine(result.interpreted_text)
                result.interpreted_text = refined_text
                result.interpreted_chars = len(refined_text)
                checkpoint.mark_done(section.id, result)
                logger.info("%s 二次重写完成: %d 字", section.context_label, len(refined_text))

                results.append(result)
                prev_text = result.interpreted_text
                update_progress(skipped=False)

            return results

        except Exception as e:
            with counter_lock:
                if first_error is None:
                    first_error = e
            error_event.set()
            raise

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_chapter = {
            executor.submit(process_chapter, ch_idx, chap_sections): ch_idx
            for ch_idx, chap_sections in chapter_sections.items()
        }

        for future in as_completed(future_to_chapter):
            ch_idx = future_to_chapter[future]
            try:
                results = future.result()
                if results is not None:
                    all_results[ch_idx] = results
            except InterpretError as e:
                error_event.set()
                pbar.close()
                click.echo(f"\n解读失败: 第 {ch_idx + 1} 章: {e.message}", err=True)
                click.echo("你可以重新运行此命令从断点恢复。", err=True)
                sys.exit(1)
            except Exception as e:
                error_event.set()
                pbar.close()
                click.echo(f"\n发生未预期的错误（第 {ch_idx + 1} 章）: {e}", err=True)
                sys.exit(1)

    pbar.close()

    click.echo(f"\n解读完成: 成功 {counters['success']} 块, 跳过 {counters['skip']} 块。")

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
