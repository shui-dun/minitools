"""格式转换模块。

将 MOBI/AZW3 等格式统一转为 EPUB，便于后续处理。
EPUB 格式直接透传。

依赖 Calibre CLI（ebook-convert）进行转换。
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# 支持的输入格式
SUPPORTED_INPUT_FORMATS = {".epub", ".mobi", ".azw3", ".azw"}

# 需要转换为 EPUB 的格式
_CONVERT_FORMATS = {".mobi", ".azw3", ".azw"}


class ConversionError(Exception):
    """格式转换失败。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CalibreNotFoundError(ConversionError):
    """Calibre CLI 未安装。"""

    def __init__(self) -> None:
        super().__init__(
            "未找到 Calibre 命令行工具 ebook-convert。\n"
            "请安装 Calibre：https://calibre-ebook.com/download\n"
            "安装后确保 ebook-convert 在系统 PATH 中。"
        )


class FormatConverter:
    """将各种电子书格式统一转换为 EPUB。

    用法：
        converter = FormatConverter()
        epub_path = converter.convert("book.mobi")
        # 返回转换后的 EPUB 路径
    """

    # 类级别缓存：避免重复检测 Calibre 是否安装
    _calibre_available: bool | None = None

    def __init__(self) -> None:
        self._check_calibre()

    def convert(self, input_path: str | Path) -> Path:
        """将输入文件转换为 EPUB 格式。

        Args:
            input_path: 输入文件路径。

        Returns:
            转换后的 EPUB 文件路径（如果是 EPUB 则返回原路径）。

        Raises:
            ConversionError: 格式不支持或转换失败。
        """
        input_path = Path(input_path).resolve()

        if not input_path.exists():
            raise ConversionError(f"文件不存在: {input_path}")

        suffix = input_path.suffix.lower()
        if suffix not in SUPPORTED_INPUT_FORMATS:
            raise ConversionError(
                f"不支持的格式: {suffix}。"
                f"支持的格式: {', '.join(sorted(SUPPORTED_INPUT_FORMATS))}"
            )

        # EPUB 直接透传
        if suffix == ".epub":
            logger.info("EPUB 格式，直接透传: %s", input_path)
            return input_path

        # MOBI/AZW3 → 通过 Calibre 转为 EPUB
        return self._convert_with_calibre(input_path)

    def _convert_with_calibre(self, input_path: Path) -> Path:
        """使用 Calibre CLI 将文件转为 EPUB。"""
        if not self._calibre_available:
            raise CalibreNotFoundError()

        output_path = input_path.with_suffix(".epub")

        # 如果输出已存在且比输入新，跳过转换
        if output_path.exists() and output_path.stat().st_mtime > input_path.stat().st_mtime:
            logger.info("EPUB 已存在且较新，跳过转换: %s", output_path)
            return output_path

        logger.info("正在转换 %s → EPUB ...", input_path.name)
        cmd = [
            "ebook-convert",
            str(input_path),
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )
            if result.returncode != 0:
                stderr = result.stderr.strip() or result.stdout.strip()
                raise ConversionError(f"Calibre 转换失败: {stderr}")

            if not output_path.exists():
                raise ConversionError("转换完成但未生成 EPUB 文件")

            logger.info("转换完成: %s", output_path)
            return output_path

        except subprocess.TimeoutExpired:
            raise ConversionError("Calibre 转换超时（超过 5 分钟）")
        except FileNotFoundError:
            raise CalibreNotFoundError()

    @classmethod
    def _check_calibre(cls) -> None:
        """检测 Calibre CLI 是否可用。"""
        if cls._calibre_available is not None:
            return
        cls._calibre_available = shutil.which("ebook-convert") is not None
        if not cls._calibre_available:
            logger.warning("Calibre ebook-convert 未安装，MOBI/AZW3 格式无法处理")
        else:
            logger.info("检测到 Calibre ebook-convert 可用")
