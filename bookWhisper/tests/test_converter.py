"""converter.py 单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookwhisper.converter import (
    ConversionError,
    FormatConverter,
    SUPPORTED_INPUT_FORMATS,
)


class TestFormatConverter:
    """格式转换测试。"""

    def test_epub_pass_through_real(self, real_epub_path: Path) -> None:
        """真实 EPUB 格式应直接透传。"""
        converter = FormatConverter()
        result = converter.convert(real_epub_path)
        assert result == real_epub_path.resolve()
        assert result.suffix == ".epub"

    def test_epub_pass_through_synthetic(self, sample_epub_path: Path) -> None:
        """合成 EPUB 也正确透传。"""
        converter = FormatConverter()
        result = converter.convert(sample_epub_path)
        assert result == sample_epub_path

    def test_unsupported_format(self, tmp_path: Path) -> None:
        """不支持的格式应抛出 ConversionError。"""
        docx_path = tmp_path / "test.docx"
        docx_path.write_text("fake docx content")
        converter = FormatConverter()
        with pytest.raises(ConversionError, match="不支持的格式"):
            converter.convert(docx_path)

    def test_file_not_found(self) -> None:
        """不存在的文件应抛出 ConversionError。"""
        converter = FormatConverter()
        with pytest.raises(ConversionError, match="文件不存在"):
            converter.convert("/nonexistent/file.epub")

    def test_file_not_found_relative(self, tmp_path: Path) -> None:
        """相对路径的不存在文件也应抛出错误。"""
        converter = FormatConverter()
        nonexistent = tmp_path / "does_not_exist.epub"
        with pytest.raises(ConversionError, match="文件不存在"):
            converter.convert(nonexistent)

    def test_supported_formats_list(self) -> None:
        """支持的格式列表应包含 EPUB、MOBI、AZW3、AZW。"""
        assert ".epub" in SUPPORTED_INPUT_FORMATS
        assert ".mobi" in SUPPORTED_INPUT_FORMATS
        assert ".azw3" in SUPPORTED_INPUT_FORMATS
        assert ".azw" in SUPPORTED_INPUT_FORMATS
