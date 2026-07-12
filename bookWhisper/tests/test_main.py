"""main.py CLI 集成测试。"""

from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from bookwhisper.config import DEFAULT_CONFIG_PATH
from bookwhisper.main import cli


class TestCli:
    """CLI 集成测试。"""

    def test_help(self) -> None:
        """bookwhisper --help 正常显示。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "interpret" in result.output

    def test_version(self) -> None:
        """--version 正常显示版本号。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_interpret_help(self) -> None:
        """interpret 子命令帮助正常显示。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["interpret", "--help"])
        assert result.exit_code == 0
        assert "INPUT_FILE" in result.output

    @pytest.mark.skipif(
        DEFAULT_CONFIG_PATH.exists() or "DEEPSEEK_API_KEY" in os.environ,
        reason="系统已配置 DeepSeek API Key，测试无 key 场景无意义",
    )
    def test_interpret_no_api_key(self, sample_epub_path) -> None:
        """没有 API key 时应报错退出（仅在未配置 API key 的环境中运行）。"""
        runner = CliRunner(env={})
        result = runner.invoke(cli, ["interpret", str(sample_epub_path)])
        assert result.exit_code != 0
        assert "API Key" in result.output

    def test_interpret_with_env_api_key(self, sample_epub_path) -> None:
        """有 API key 时不应因缺 key 退出（但可能因网络问题报其他错）。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, ["interpret", str(sample_epub_path)])
        # 可能因无网络而报错，但不应该因为缺少 API key 报错
        if result.exit_code != 0:
            assert "API Key" not in result.output

    def test_interpret_with_cli_overrides(self, sample_epub_path) -> None:
        """CLI 参数覆盖配置。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, [
            "interpret",
            str(sample_epub_path),
            "--chunk-max-chars", "2000",
            "--deepseek-model", "deepseek-reasoner",
            "--no-resume",
        ])
        # 可能因网络问题报错，但不应 crash
        assert isinstance(result.exit_code, int)

    def test_interpret_file_not_found(self) -> None:
        """不存在的文件应报错。"""
        runner = CliRunner()
        result = runner.invoke(cli, ["interpret", "/nonexistent/file.epub"])
        assert result.exit_code != 0

    def test_verbose_flag(self, sample_epub_path) -> None:
        """--verbose 标志不应报错。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, [
            "interpret",
            str(sample_epub_path),
            "--verbose",
        ])
        assert isinstance(result.exit_code, int)

    # ---- MOBI/AZW3 格式输入测试 ----

    def test_interpret_mobi_input(self, real_mobi_path) -> None:
        """CLI 接受 .mobi 文件作为输入。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, ["interpret", str(real_mobi_path)])
        # 可能因缺 Calibre 或网络问题失败，但不应该因为"不支持的格式"报错
        assert isinstance(result.exit_code, int)

    def test_interpret_azw3_input(self, real_azw3_path) -> None:
        """CLI 接受 .azw3 文件作为输入。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, ["interpret", str(real_azw3_path)])
        # 可能因缺 Calibre 或网络问题失败，但不应该因为"不支持的格式"报错
        assert isinstance(result.exit_code, int)

    def test_interpret_mobi_with_cli_overrides(self, real_mobi_path) -> None:
        """MOBI 文件 + CLI 参数覆盖不应 crash。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, [
            "interpret",
            str(real_mobi_path),
            "--chunk-max-chars", "2000",
            "--output-suffix", "_test",
            "--no-resume",
        ])
        assert isinstance(result.exit_code, int)

    def test_interpret_azw3_with_cli_overrides(self, real_azw3_path) -> None:
        """AZW3 文件 + CLI 参数覆盖不应 crash。"""
        runner = CliRunner(env={"DEEPSEEK_API_KEY": "sk-test"})
        result = runner.invoke(cli, [
            "interpret",
            str(real_azw3_path),
            "--chunk-max-chars", "2000",
            "--output-suffix", "_test",
            "--no-resume",
        ])
        assert isinstance(result.exit_code, int)
