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
from bookwhisper.main import _discover_book_files, _batch_interpret, cli


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

    def test_serial_execution_order(self, tmp_path: Path) -> None:
        """验证书籍按文件名排序串行处理。"""
        (tmp_path / "c.epub").write_text("dummy")
        (tmp_path / "a.epub").write_text("dummy")
        (tmp_path / "b.epub").write_text("dummy")
        config = AppConfig()

        processed = []

        def side_effect(book_path, *args, **kwargs):
            processed.append(book_path.name)

        with mock.patch("bookwhisper.main._run_pipeline", side_effect=side_effect):
            with mock.patch("click.echo"):
                _batch_interpret(tmp_path, config)
                assert processed == ["a.epub", "b.epub", "c.epub"], \
                    f"期望按文件名排序处理，实际顺序: {processed}"


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

    def test_nonexistent_directory(self) -> None:
        """不存在的目录应被 click.Path(exists=True) 拦截。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["interpret", "/nonexistent/directory/path"])
        assert result.exit_code != 0
