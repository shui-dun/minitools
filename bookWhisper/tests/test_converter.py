"""converter.py 单元测试。

覆盖场景：
- EPUB 透传
- MOBI/AZW3 格式识别
- Calibre 转换（mock）
- 各种错误场景
- 真实 MOBI/AZW3 文件测试
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

import pytest

from bookwhisper.converter import (
    SUPPORTED_INPUT_FORMATS,
    CalibreNotFoundError,
    ConversionError,
    FormatConverter,
)


# ==================== EPUB 透传测试 ====================


class TestEpubPassThrough:
    """EPUB 格式直接透传，不触发转换。"""

    def test_real_epub_pass_through(self, real_epub_path: Path) -> None:
        """真实 EPUB 应原样返回。"""
        converter = FormatConverter()
        result = converter.convert(real_epub_path)
        assert result == real_epub_path.resolve()
        assert result.suffix == ".epub"

    def test_synthetic_epub_pass_through(self, sample_epub_path: Path) -> None:
        """合成 EPUB 也应原样返回。"""
        converter = FormatConverter()
        result = converter.convert(sample_epub_path)
        assert result == sample_epub_path


# ==================== 格式识别测试 ====================


class TestFormatDetection:
    """验证对不同文件格式的识别能力。"""

    def test_mobi_is_accepted(self, real_mobi_path: Path) -> None:
        """MOBI 格式应在支持列表中，convert() 不应因"不支持的格式"报错。"""
        assert ".mobi" in SUPPORTED_INPUT_FORMATS
        converter = FormatConverter()
        # Calibre 可能已安装也可能未安装，无论哪种情况都不应报"不支持的格式"
        try:
            result = converter.convert(real_mobi_path)
            # 如果 Calibre 可用，转换成功，验证返回 EPUB 路径
            assert result.suffix == ".epub"
        except CalibreNotFoundError:
            # Calibre 不可用，这是可接受的
            pass
        except ConversionError as e:
            # 其他转换错误也不应是"不支持的格式"
            assert "不支持的格式" not in str(e)

    def test_azw3_is_accepted(self, real_azw3_path: Path) -> None:
        """AZW3 格式应在支持列表中，convert() 不应因"不支持的格式"报错。"""
        assert ".azw3" in SUPPORTED_INPUT_FORMATS
        converter = FormatConverter()
        try:
            result = converter.convert(real_azw3_path)
            assert result.suffix == ".epub"
        except CalibreNotFoundError:
            pass
        except ConversionError as e:
            assert "不支持的格式" not in str(e)

    def test_supported_formats_list_complete(self) -> None:
        """支持的格式列表应包含 EPUB、MOBI、AZW3、AZW。"""
        assert ".epub" in SUPPORTED_INPUT_FORMATS
        assert ".mobi" in SUPPORTED_INPUT_FORMATS
        assert ".azw3" in SUPPORTED_INPUT_FORMATS
        assert ".azw" in SUPPORTED_INPUT_FORMATS

    def test_unsupported_format(self, tmp_path: Path) -> None:
        """不支持的格式应抛出 ConversionError。"""
        docx_path = tmp_path / "test.docx"
        docx_path.write_text("fake docx content")
        converter = FormatConverter()
        with pytest.raises(ConversionError, match="不支持的格式"):
            converter.convert(docx_path)

    @pytest.mark.parametrize("ext", [".MOBI", ".Mobi", ".Azw3", ".AZW3", ".EPUB", ".Epub"])
    def test_case_insensitive_suffix(self, tmp_path: Path, ext: str) -> None:
        """文件后缀应大小写不敏感。"""
        f = tmp_path / f"test_book{ext}"
        f.write_text("dummy content")
        converter = FormatConverter()
        # EPUB 大小写变体 → 应透传
        # MOBI/AZW3 大小写变体 → 应触发转换（可能因缺 Calibre 报错，但不应报"不支持的格式"）
        try:
            result = converter.convert(f)
            # 如果是透传的 EPUB，验证路径
            if ext.lower() == ".epub":
                assert result.suffix.lower() == ".epub"
        except CalibreNotFoundError:
            # 这是 MOBI/AZW3 大小写变体，Calibre 不可用时预期行为
            pass
        except ConversionError as e:
            # 不应是"不支持的格式"
            assert "不支持的格式" not in str(e)


# ==================== 错误处理测试 ====================


class TestErrorHandling:
    """验证各种错误场景。"""

    def test_file_not_found_absolute(self) -> None:
        """不存在的绝对路径文件应抛出 ConversionError。"""
        converter = FormatConverter()
        with pytest.raises(ConversionError, match="文件不存在"):
            converter.convert("/nonexistent/file.epub")

    def test_file_not_found_relative(self, tmp_path: Path) -> None:
        """不存在的相对路径文件也应抛出错误。"""
        converter = FormatConverter()
        nonexistent = tmp_path / "does_not_exist.epub"
        with pytest.raises(ConversionError, match="文件不存在"):
            converter.convert(nonexistent)

    def test_calibre_not_found_for_non_epub(self, tmp_path: Path) -> None:
        """Calibre 未安装时转换 MOBI 应抛出 CalibreNotFoundError。"""
        mobi_path = tmp_path / "test.mobi"
        mobi_path.write_text("dummy mobi content")
        converter = FormatConverter()
        # 重置类级别缓存，模拟 Calibre 不可用
        FormatConverter._calibre_available = False
        try:
            with pytest.raises(CalibreNotFoundError):
                converter.convert(mobi_path)
        finally:
            # 恢复缓存状态
            FormatConverter._calibre_available = None


# ==================== Mock Calibre 转换测试 ====================


class TestMockedCalibreConversion:
    """使用 mock 模拟 Calibre CLI，验证 _convert_with_calibre 的各个分支。"""

    @pytest.fixture(autouse=True)
    def reset_calibre_cache(self) -> None:
        """每个测试前后重置 Calibre 可用性缓存。"""
        FormatConverter._calibre_available = None
        yield
        FormatConverter._calibre_available = None

    def test_mobi_conversion_success(self, tmp_path: Path) -> None:
        """Mock Calibre 成功将 MOBI 转为 EPUB。"""
        mobi_path = tmp_path / "book.mobi"
        mobi_path.write_text("fake mobi content")

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = ""

                # side effect: 模拟 Calibre 实际生成 EPUB 文件
                def create_output(*args, **kwargs):
                    mobi_path.with_suffix(".epub").write_text("converted content")
                    return mock.DEFAULT

                mock_run.side_effect = create_output

                converter = FormatConverter()
                result = converter.convert(mobi_path)

                # 验证返回的是 .epub 路径
                assert result.suffix == ".epub"
                assert result.name == "book.epub"

                # 验证 ebook-convert 被正确调用
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "ebook-convert"
                assert cmd[1] == str(mobi_path)

    def test_azw3_conversion_success(self, tmp_path: Path) -> None:
        """Mock Calibre 成功将 AZW3 转为 EPUB。"""
        azw3_path = tmp_path / "book.azw3"
        azw3_path.write_text("fake azw3 content")

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = ""

                def create_output(*args, **kwargs):
                    azw3_path.with_suffix(".epub").write_text("converted content")
                    return mock.DEFAULT

                mock_run.side_effect = create_output

                converter = FormatConverter()
                result = converter.convert(azw3_path)

                assert result.suffix == ".epub"
                assert result.name == "book.epub"
                mock_run.assert_called_once()

    def test_conversion_nonzero_exit(self, tmp_path: Path) -> None:
        """Calibre 返回非零退出码时应抛出 ConversionError。"""
        mobi_path = tmp_path / "corrupt.mobi"
        mobi_path.write_text("corrupt content")

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "Calibre conversion error: unsupported format"

                converter = FormatConverter()
                with pytest.raises(ConversionError, match="Calibre 转换失败"):
                    converter.convert(mobi_path)

    def test_conversion_timeout(self, tmp_path: Path) -> None:
        """Calibre 转换超时应抛出 ConversionError。"""
        mobi_path = tmp_path / "huge.mobi"
        mobi_path.write_text("huge file content")

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ebook-convert"], timeout=300)

                converter = FormatConverter()
                with pytest.raises(ConversionError, match="超时"):
                    converter.convert(mobi_path)

    def test_conversion_no_output_file(self, tmp_path: Path) -> None:
        """转换成功但未生成输出文件时应抛出 ConversionError。"""
        mobi_path = tmp_path / "book.mobi"
        mobi_path.write_text("fake content")

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                converter = FormatConverter()
                with pytest.raises(ConversionError, match="未生成 EPUB 文件"):
                    converter.convert(mobi_path)

    def test_calibre_not_installed(self, tmp_path: Path) -> None:
        """shutil.which 返回 None 时，转换 MOBI 应报 CalibreNotFoundError。"""
        mobi_path = tmp_path / "book.mobi"
        mobi_path.write_text("fake content")

        with mock.patch("shutil.which", return_value=None):
            # 强制重置缓存
            FormatConverter._calibre_available = None
            converter = FormatConverter()
            with pytest.raises(CalibreNotFoundError):
                converter.convert(mobi_path)

    def test_existing_epub_newer_skipped(self, tmp_path: Path) -> None:
        """输出 EPUB 已存在且比源文件新时，应跳过转换、返回已有路径。"""
        mobi_path = tmp_path / "book.mobi"
        mobi_path.write_text("source content")

        epub_path = tmp_path / "book.epub"
        epub_path.write_text("cached result content")

        # 让 EPUB 的修改时间比 MOBI 晚
        epub_stat = epub_path.stat()
        mobi_stat = mobi_path.stat()
        # 实际上 write 后 epub_path 可能更晚，但保险起见调整
        import os
        os.utime(str(epub_path), (mobi_stat.st_mtime + 10, mobi_stat.st_mtime + 10))
        os.utime(str(mobi_path), (mobi_stat.st_mtime, mobi_stat.st_mtime))

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                converter = FormatConverter()
                result = converter.convert(mobi_path)

                # 应跳过转换
                mock_run.assert_not_called()
                assert result == epub_path

    def test_existing_epub_older_replaced(self, tmp_path: Path) -> None:
        """输出 EPUB 已存在但比源文件旧时，应重新转换。"""
        import os

        mobi_path = tmp_path / "book.mobi"
        mobi_path.write_text("source content")

        epub_path = tmp_path / "book.epub"
        epub_path.write_text("old result")

        # 让 EPUB 的修改时间比 MOBI 早
        os.utime(str(epub_path), (1000000000, 1000000000))
        os.utime(str(mobi_path), (2000000000, 2000000000))

        with mock.patch("shutil.which", return_value="/usr/bin/ebook-convert"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = ""

                # 模拟：转换后 epub_path 真实存在
                def side_effect(*args, **kwargs):
                    epub_path.write_text("new result")
                    return mock.DEFAULT
                mock_run.side_effect = side_effect

                converter = FormatConverter()
                result = converter.convert(mobi_path)

                # 应执行转换
                mock_run.assert_called_once()
                assert result == epub_path


# ==================== 真实文件集成测试 ====================


class TestRealFileIntegration:
    """使用真实 MOBI/AZW3 文件验证端到端行为。"""

    def test_real_mobi_exists_and_valid(self, real_mobi_path: Path) -> None:
        """真实 MOBI 文件存在、非空、后缀正确。"""
        assert real_mobi_path.exists()
        assert real_mobi_path.is_file()
        assert real_mobi_path.stat().st_size > 0
        assert real_mobi_path.suffix.lower() == ".mobi"

    def test_real_azw3_exists_and_valid(self, real_azw3_path: Path) -> None:
        """真实 AZW3 文件存在、非空、后缀正确。"""
        assert real_azw3_path.exists()
        assert real_azw3_path.is_file()
        assert real_azw3_path.stat().st_size > 0
        assert real_azw3_path.suffix.lower() == ".azw3"

    def test_real_mobi_converts_or_reports_error(self, real_mobi_path: Path) -> None:
        """真实 MOBI 文件转换：Calibre 可用则成功，不可用则明确报错。"""
        converter = FormatConverter()
        try:
            result = converter.convert(real_mobi_path)
            # 如果成功，验证结果是 EPUB
            assert result.suffix == ".epub"
            assert result.exists()
        except CalibreNotFoundError:
            # Calibre 不可用，这是可接受的
            pass
        except ConversionError as e:
            # 其他转换错误（如文件格式问题）
            # 不应是"不支持的格式"
            assert "不支持的格式" not in str(e)

    def test_real_azw3_converts_or_reports_error(self, real_azw3_path: Path) -> None:
        """真实 AZW3 文件转换：Calibre 可用则成功，不可用则明确报错。"""
        converter = FormatConverter()
        try:
            result = converter.convert(real_azw3_path)
            assert result.suffix == ".epub"
            assert result.exists()
        except CalibreNotFoundError:
            pass
        except ConversionError as e:
            assert "不支持的格式" not in str(e)


# ==================== ConversionError 测试 ====================


class TestConversionError:
    """ConversionError / CalibreNotFoundError 的错误信息。"""

    def test_conversion_error_message(self) -> None:
        """ConversionError 应正确保存 message。"""
        err = ConversionError("测试错误")
        assert err.message == "测试错误"
        assert str(err) == "测试错误"

    def test_calibre_not_found_message(self) -> None:
        """CalibreNotFoundError 应包含安装指引。"""
        err = CalibreNotFoundError()
        assert "ebook-convert" in err.message
        assert "calibre" in err.message.lower()
