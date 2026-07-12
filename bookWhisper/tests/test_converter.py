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

    def test_epub_pass_through(self, sample_epub_path: Path) -> None:
        """EPUB 格式应直接透传。"""
        converter = FormatConverter()
        result = converter.convert(sample_epub_path)
        assert result == sample_epub_path
        assert result.suffix == ".epub"

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

    def test_supported_formats_list(self) -> None:
        """支持的格式列表应包含 EPUB、MOBI、AZW3。"""
        assert ".epub" in SUPPORTED_INPUT_FORMATS
        assert ".mobi" in SUPPORTED_INPUT_FORMATS
        assert ".azw3" in SUPPORTED_INPUT_FORMATS
