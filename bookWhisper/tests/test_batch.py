"""批量翻译功能单元测试。

覆盖:
- _discover_book_files: 目录递归扫描、格式过滤、排序去重
- _batch_interpret: 串行处理、失败继续、成功计数
- CLI 集成: 目录参数触发批量模式
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from bookwhisper.config import AppConfig
from bookwhisper.main import _discover_book_files, _filter_batch_books, _batch_interpret, cli


# ==================== _discover_book_files 测试 ====================


class TestDiscoverBookFiles:
    """测试 _discover_book_files 函数的递归扫描逻辑。"""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """空目录应返回空列表。"""
        result = _discover_book_files(tmp_path)
        assert result == []

    def test_single_epub(self, tmp_path: Path) -> None:
        """包含单个 EPUB 的目录应找到该文件。"""
        book = tmp_path / "测试书.epub"
        book.write_text("dummy")
        result = _discover_book_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "测试书.epub"

    def test_multiple_formats(self, tmp_path: Path) -> None:
        """混合多种格式的目录应找到所有电子书。"""
        formats = [".epub", ".mobi", ".azw3", ".azw"]
        for fmt in formats:
            (tmp_path / f"book{fmt}").write_text("dummy")
        # 添加几个非电子书文件
        (tmp_path / "readme.txt").write_text("not a book")
        (tmp_path / "notes.pdf").write_text("not a book")
        result = _discover_book_files(tmp_path)
        assert len(result) == 4

    def test_case_insensitive_extensions(self, tmp_path: Path) -> None:
        """文件后缀应大小写不敏感。"""
        (tmp_path / "book.EPUB").write_text("dummy")
        (tmp_path / "book.MOBI").write_text("dummy")
        (tmp_path / "book.Azw3").write_text("dummy")
        result = _discover_book_files(tmp_path)
        assert len(result) == 3

    def test_recursive_scan(self, tmp_path: Path) -> None:
        """应递归扫描嵌套子目录。"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root_book.epub").write_text("dummy")
        (subdir / "nested_book.epub").write_text("dummy")
        result = _discover_book_files(tmp_path)
        assert len(result) == 2

    def test_sorted_by_name(self, tmp_path: Path) -> None:
        """结果应按文件名排序。"""
        (tmp_path / "c.epub").write_text("dummy")
        (tmp_path / "a.epub").write_text("dummy")
        (tmp_path / "b.mobi").write_text("dummy")
        result = _discover_book_files(tmp_path)
        names = [r.name for r in result]
        assert names == ["a.epub", "b.mobi", "c.epub"]

    def test_no_supported_formats(self, tmp_path: Path) -> None:
        """目录中只有不支持的文件格式时返回空列表。"""
        (tmp_path / "doc.txt").write_text("dummy")
        (tmp_path / "presentation.pdf").write_text("dummy")
        (tmp_path / "image.png").write_text("dummy")
        result = _discover_book_files(tmp_path)
        assert result == []

    def test_deduplication(self, tmp_path: Path) -> None:
        """同名不同路径的文件去重（通过解析后的绝对路径）。"""
        # 在 Windows 上 rglob 不会产生重复，但确保去重逻辑健壮
        (tmp_path / "book.epub").write_text("dummy")
        result = _discover_book_files(tmp_path)
        assert len(result) == 1

    def test_hidden_files_not_excluded(self, tmp_path: Path) -> None:
        """隐藏文件（如 .开头）如果是支持的格式也应被发现。"""
        (tmp_path / ".hidden_book.epub").write_text("dummy")
        result = _discover_book_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == ".hidden_book.epub"


# ==================== _filter_batch_books 测试 ====================


class TestFilterBatchBooks:
    """测试 _filter_batch_books 的过滤和去重逻辑。"""

    DEFAULT_SUFFIX = "_interpreted"

    def _make_books(self, tmp_path: Path, *names: str) -> list[Path]:
        """在临时目录创建指定文件名的空文件，返回 Path 列表（保持 _discover_book_files 的排序）。"""
        books = []
        for name in names:
            p = tmp_path / name
            p.write_text("dummy")
            books.append(p)
        return sorted(books, key=lambda p: p.name.lower())

    def test_empty_list(self) -> None:
        """空列表返回空列表。"""
        assert _filter_batch_books([], self.DEFAULT_SUFFIX) == []

    def test_normal_books_unchanged(self, tmp_path: Path) -> None:
        """不涉及输出后缀和同名冲突时，所有书籍保留。"""
        books = self._make_books(tmp_path, "a.epub", "b.mobi", "c.azw3")
        result = _filter_batch_books(books, self.DEFAULT_SUFFIX)
        assert len(result) == 3

    def test_exclude_output_files(self, tmp_path: Path) -> None:
        """stem 以 output_suffix 结尾的文件应被排除。"""
        books = self._make_books(
            tmp_path,
            "a.epub",                    # 正常文件，保留
            "a_interpreted.epub",        # 输出文件，排除
            "b_interpreted.epub",        # 输出文件，排除
            "c.mobi",                    # 正常文件，保留
        )
        result = _filter_batch_books(books, self.DEFAULT_SUFFIX)
        names = [r.name for r in result]
        assert names == ["a.epub", "c.mobi"]
        assert "a_interpreted.epub" not in names
        assert "b_interpreted.epub" not in names

    def test_dedup_epub_preferred(self, tmp_path: Path) -> None:
        """同名不同格式时保留 EPUB，跳过其他格式。"""
        books = self._make_books(
            tmp_path,
            "book.epub",    # EPUB 优先
            "book.mobi",    # 应被跳过（同名 EPUB 已存在）
            "book.azw3",    # 应被跳过
        )
        result = _filter_batch_books(books, self.DEFAULT_SUFFIX)
        names = [r.name for r in result]
        assert names == ["book.epub"]

    def test_no_epub_first_format_wins(self, tmp_path: Path) -> None:
        """没有 EPUB 时保留第一个发现的格式。"""
        books = self._make_books(
            tmp_path,
            "book.mobi",
            "book.azw3",
        )
        result = _filter_batch_books(books, self.DEFAULT_SUFFIX)
        assert len(result) == 1
        assert result[0].suffix in (".mobi", ".azw3")

    def test_dedup_does_not_affect_different_stems(self, tmp_path: Path) -> None:
        """不同 stem 的文件不受去重影响。"""
        books = self._make_books(
            tmp_path,
            "alpha.epub",
            "beta.epub",
            "gamma.mobi",
            "alpha.mobi",    # 与 alpha.epub 同名，应跳过
        )
        result = _filter_batch_books(books, self.DEFAULT_SUFFIX)
        names = [r.name for r in result]
        assert "alpha.epub" in names
        assert "beta.epub" in names
        assert "gamma.mobi" in names
        assert "alpha.mobi" not in names  # 被去重

    def test_output_suffix_and_dedup_combined(self, tmp_path: Path) -> None:
        """输出文件排除和去重同时生效。"""
        books = self._make_books(
            tmp_path,
            "book.epub",                  # 保留（正常 EPUB）
            "book.mobi",                  # 跳过（同名 EPUB 存在）
            "book_interpreted.epub",      # 跳过（输出文件）
            "other_interpreted.epub",     # 跳过（输出文件）
            "other.mobi",                 # 保留（唯一格式，无同名 EPUB）
        )
        result = _filter_batch_books(books, self.DEFAULT_SUFFIX)
        names = [r.name for r in result]
        assert names == ["book.epub", "other.mobi"]

    def test_custom_suffix(self, tmp_path: Path) -> None:
        """使用自定义后缀过滤。"""
        books = self._make_books(
            tmp_path,
            "normal.epub",
            "normal_custom.epub",     # 自定义后缀 → 排除
            "normal_interpreted.epub", # 默认后缀 → 不排除（因为改用了自定义后缀）
        )
        result = _filter_batch_books(books, "_custom")
        names = [r.name for r in result]
        assert "normal.epub" in names
        assert "normal_interpreted.epub" in names
        assert "normal_custom.epub" not in names

    def test_suffix_mid_stem_not_excluded(self, tmp_path: Path) -> None:
        """后缀出现在 stem 中间（非末尾）时不应被排除。"""
        # stem = "my_interpreted_book"，中间有 _interpreted 但不是结尾
        books = self._make_books(tmp_path, "my_interpreted_book.epub")
        result = _filter_batch_books(books, "_interpreted")
        # stem "my_interpreted_book" 不以 "_interpreted" 结尾，应保留
        assert len(result) == 1


# ==================== _batch_interpret 测试 ====================


class TestBatchInterpret:
    """测试 _batch_interpret 函数的串行处理和容错逻辑。"""

    def test_no_books_found(self, tmp_path: Path) -> None:
        """目录中没有电子书时应打印警告，不调用 pipeline。"""
        config = AppConfig()
        with mock.patch("bookwhisper.main._run_pipeline") as mock_run:
            with mock.patch("click.echo") as mock_echo:
                _batch_interpret(tmp_path, config)
                mock_run.assert_not_called()
                # 验证打印了警告信息
                warning_found = False
                for call in mock_echo.call_args_list:
                    arg = call[0][0] if call[0] else ""
                    if "未找到" in str(arg):
                        warning_found = True
                assert warning_found, "应打印'未找到任何支持的电子书文件'警告"

    def test_single_book_success(self, tmp_path: Path) -> None:
        """单本书成功翻译时应调用一次 pipeline。"""
        (tmp_path / "book.epub").write_text("dummy")
        config = AppConfig()
        with mock.patch("bookwhisper.main._run_pipeline") as mock_run:
            _batch_interpret(tmp_path, config)
            mock_run.assert_called_once()

    def test_multiple_books_all_success(self, tmp_path: Path) -> None:
        """多本书全部成功时 pipeline 应被调用等于书籍数量次。"""
        for name in ["a.epub", "b.epub", "c.mobi"]:
            (tmp_path / name).write_text("dummy")
        config = AppConfig()
        with mock.patch("bookwhisper.main._run_pipeline") as mock_run:
            _batch_interpret(tmp_path, config)
            assert mock_run.call_count == 3

    def test_book_fails_with_system_exit_continues(self, tmp_path: Path) -> None:
        """一本书触发 SystemExit 后应继续处理下一本。"""
        (tmp_path / "a.epub").write_text("dummy")
        (tmp_path / "b.epub").write_text("dummy")
        config = AppConfig()

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise SystemExit(1)
            # 第二本不抛异常

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                _batch_interpret(tmp_path, config)
                # 两本都应被处理
                assert call_count == 2

    def test_book_fails_with_exception_continues(self, tmp_path: Path) -> None:
        """一本书抛出普通异常后应继续处理下一本。"""
        (tmp_path / "a.epub").write_text("dummy")
        (tmp_path / "b.epub").write_text("dummy")
        config = AppConfig()

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("模拟的翻译失败")
            # 第二本不抛异常

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                _batch_interpret(tmp_path, config)
                assert call_count == 2

    def test_all_books_fail_still_completes(self, tmp_path: Path) -> None:
        """所有书都失败时函数仍应正常返回，不向上抛异常。"""
        for name in ["a.epub", "b.epub", "c.epub"]:
            (tmp_path / name).write_text("dummy")
        config = AppConfig()

        with mock.patch(
            "bookwhisper.main._run_pipeline", side_effect=SystemExit(1)
        ):
            with mock.patch("click.echo"):
                # 不应抛异常
                try:
                    _batch_interpret(tmp_path, config)
                except Exception as e:
                    pytest.fail(f"_batch_interpret 不应抛异常，但抛出了: {e}")

    def test_all_books_processed(self, tmp_path: Path) -> None:
        """验证所有书籍都被处理（并发模式下顺序不保证）。"""
        (tmp_path / "c.epub").write_text("dummy")
        (tmp_path / "a.epub").write_text("dummy")
        (tmp_path / "b.epub").write_text("dummy")
        config = AppConfig()

        processed: list[str] = []
        lock = __import__("threading").Lock()

        def side_effect(book_path, *args, **kwargs):
            with lock:
                processed.append(book_path.name)

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                _batch_interpret(tmp_path, config)
                assert sorted(processed) == ["a.epub", "b.epub", "c.epub"], \
                    f"所有三本书都应被处理，实际: {processed}"

    def test_concurrent_processing(self, tmp_path: Path) -> None:
        """验证多本书确实并发执行（总耗时 < 串行耗时）。"""
        import time

        # 创建 3 本书
        for name in ["a.epub", "b.epub", "c.epub"]:
            (tmp_path / name).write_text("dummy")

        config = AppConfig()
        config.batch_workers = 3  # 允许 3 本并发

        sleep_time = 0.1  # 每本书 sleep 0.1 秒

        def side_effect(book_path, *args, **kwargs):
            time.sleep(sleep_time)
            return book_path  # 不抛异常

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                start = time.monotonic()
                _batch_interpret(tmp_path, config)
                elapsed = time.monotonic() - start

        # 并发 3 本应 < 串行 3 × 0.1 = 0.3，给 0.25 留余量
        assert elapsed < sleep_time * 2.5, \
            f"并发耗时 ({elapsed:.2f}s) 应远小于串行 (0.3s)"

    def test_batch_workers_capped_by_config(self, tmp_path: Path) -> None:
        """验证并发度不超过 batch_workers 设置。"""
        import time

        for name in [f"book_{i:02d}.epub" for i in range(6)]:
            (tmp_path / name).write_text("dummy")

        config = AppConfig()
        config.batch_workers = 2  # 最多 2 本并发

        max_concurrent = 0
        current = 0
        lock = __import__("threading").Lock()

        def side_effect(book_path, *args, **kwargs):
            nonlocal max_concurrent, current
            with lock:
                current += 1
                if current > max_concurrent:
                    max_concurrent = current
            time.sleep(0.05)
            with lock:
                current -= 1

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                _batch_interpret(tmp_path, config)

        assert max_concurrent <= 2, \
            f"最大并发数 ({max_concurrent}) 应不超过 batch_workers (2)"

    def test_concurrent_with_failures(self, tmp_path: Path) -> None:
        """并发模式下部分失败仍能全部完成。"""
        for name in ["a.epub", "b.epub", "c.epub", "d.epub"]:
            (tmp_path / name).write_text("dummy")

        config = AppConfig()
        config.batch_workers = 4

        call_count = 0
        lock = __import__("threading").Lock()

        def side_effect(book_path, *args, **kwargs):
            nonlocal call_count
            with lock:
                call_count += 1
                current = call_count
            if current % 2 == 1:  # 第 1、3 本失败
                raise SystemExit(1)
            # 第 2、4 本成功

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                _batch_interpret(tmp_path, config)
                # 4 本全部被处理
                assert call_count == 4


# ==================== CLI 集成测试 ====================


class TestCliBatchMode:
    """测试 CLI interpret 命令的批量模式入口。"""

    def test_directory_triggers_batch_mode(self, tmp_path: Path) -> None:
        """传入目录应触发批量翻译模式。"""
        (tmp_path / "book.epub").write_text("dummy")
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        with mock.patch("bookwhisper.main._run_pipeline") as mock_run:
            result = runner.invoke(cli, ["interpret", str(tmp_path)])
            # 批量模式不应因缺 API key 报错（key 已设置）
            # pipeline 会被调用一次（mock 阻止了实际 API 调用）
            mock_run.assert_called_once()
            assert "批量翻译模式" in result.output

    def test_empty_directory_warns(self, tmp_path: Path) -> None:
        """空目录应打印警告并正常退出。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, ["interpret", str(tmp_path)])
        assert result.exit_code == 0
        assert "未找到" in result.output

    def test_directory_with_no_books(self, tmp_path: Path) -> None:
        """目录中存在文件但无支持的电子书格式，应打印警告。"""
        (tmp_path / "readme.txt").write_text("hello")
        (tmp_path / "data.csv").write_text("col1,col2")
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, ["interpret", str(tmp_path)])
        assert result.exit_code == 0
        assert "未找到" in result.output

    def test_directory_with_api_key_check(self, tmp_path: Path) -> None:
        """目录模式下仍需校验 API Key。"""
        (tmp_path / "book.epub").write_text("dummy")
        # 清除环境变量中的 API Key
        runner = CliRunner(env={})
        with mock.patch.dict(os.environ, {}, clear=True):
            # 确保 _BATCH_INTERPRET 不会被调到（会先因缺 key 退出）
            result = runner.invoke(cli, ["interpret", str(tmp_path)])
            # 应因缺少 API Key 而退出
            assert result.exit_code != 0
            assert "API Key" in result.output

    def test_directory_with_cli_overrides(self, tmp_path: Path) -> None:
        """目录模式 + CLI 参数覆盖不应 crash。"""
        (tmp_path / "book.epub").write_text("dummy")
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        with mock.patch("bookwhisper.main._run_pipeline") as mock_run:
            result = runner.invoke(cli, [
                "interpret",
                str(tmp_path),
                "--chunk-max-chars", "2000",
                "--mode", "novel",
                "--no-resume",
                "--verbose",
            ])
            assert isinstance(result.exit_code, int)
            mock_run.assert_called_once()

    def test_batch_workers_cli_option(self, tmp_path: Path) -> None:
        """--batch-workers 参数不应 crash。"""
        (tmp_path / "book.epub").write_text("dummy")
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        with mock.patch("bookwhisper.main._run_pipeline"):
            result = runner.invoke(cli, [
                "interpret", str(tmp_path), "--batch-workers", "10",
            ])
            assert isinstance(result.exit_code, int)
            assert "并发度" in result.output

    def test_nonexistent_directory(self) -> None:
        """不存在的目录应被 click.Path(exists=True) 拦截。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["interpret", "/nonexistent/directory/path"])
        assert result.exit_code != 0
