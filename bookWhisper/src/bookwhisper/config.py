"""配置管理模块。

支持三层配置来源，按优先级从低到高：
1. 默认值（代码中定义）
2. YAML 配置文件
3. 环境变量 / CLI 点号路径参数

配置文件和环境变量/CLI 使用相同的嵌套键结构。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DeepSeekConfig:
    """DeepSeek API 配置。"""

    api_key: str = ""
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    temperature: float = 0.3
    max_tokens: int = 8192


@dataclass
class ChunkConfig:
    """文本分块配置。"""

    max_chars: int = 15000
    book_summary_chars: int = 800
    chapter_summary_chars: int = 100


@dataclass
class OutputConfig:
    """输出配置。"""

    dir: str = "./output"
    suffix: str = "_interpreted"


@dataclass
class AppConfig:
    """应用全局配置（嵌套结构）。"""

    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    # 非嵌套项
    resume: bool = True
    max_retries: int = 3
    parallel_workers: int = 5

    def as_nested_dict(self) -> dict[str, dict[str, Any]]:
        """将配置展开为嵌套字典，方便点号路径查找。

        例如 {"deepseek": {"model": "deepseek-chat", ...}, "chunk": {...}, ...}
        """
        result: dict[str, dict[str, Any]] = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if isinstance(value, (DeepSeekConfig, ChunkConfig, OutputConfig)):
                # 嵌套 dataclass → 展开为 dict
                result[field_name] = {
                    f: getattr(value, f) for f in value.__dataclass_fields__
                }
        return result

    def apply_cli_overrides(self, overrides: dict[str, str]) -> None:
        """应用 CLI 点号路径覆盖。

        Args:
            overrides: 点号路径到值的映射，如 {"deepseek.model": "deepseek-chat", "chunk.max_chars": "2000"}
            也支持顶级字段如 {"resume": "false"}。
        """
        for key, value in overrides.items():
            parts = key.split(".")
            if len(parts) == 1:
                # 顶级字段
                field_name = parts[0]
                if hasattr(self, field_name):
                    old_value = getattr(self, field_name)
                    converted = _coerce_type(value, old_value)
                    setattr(self, field_name, converted)
            elif len(parts) == 2:
                section, field_name = parts
                section_obj = getattr(self, section, None)
                if section_obj is not None and hasattr(section_obj, field_name):
                    # 类型转换：根据原字段类型转换字符串值
                    old_value = getattr(section_obj, field_name)
                    converted = _coerce_type(value, old_value)
                    setattr(section_obj, field_name, converted)


def _coerce_type(value: str, reference: Any) -> Any:
    """根据 reference 的类型将字符串 value 转换为对应类型。"""
    if isinstance(reference, bool):
        return value.lower() in ("true", "1", "yes")
    if isinstance(reference, int):
        return int(value)
    if isinstance(reference, float):
        return float(value)
    return value


def _resolve_env_vars(raw: str) -> str:
    """解析字符串中的 ${VAR} 环境变量引用。"""
    pattern = re.compile(r"\$\{(\w+)\}")
    return pattern.sub(lambda m: os.environ.get(m.group(1), ""), raw)


def _deep_update(base: dict, override: dict) -> dict:
    """深度合并两个字典，override 的值覆盖 base。"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = value
    return result


# 默认配置文件路径（家目录）
DEFAULT_CONFIG_PATH = Path.home() / ".bookwhisper.yaml"


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """加载配置。

    优先级：默认值 < 配置文件 < 环境变量

    配置文件查找顺序：
    1. 显式指定的 --config 路径
    2. 家目录 ~/.bookwhisper.yaml（如果存在）

    Args:
        config_path: YAML 配置文件路径，可选。

    Returns:
        AppConfig 实例。
    """
    config = AppConfig()

    import yaml

    # 确定要加载的配置文件路径
    paths_to_try: list[Path] = []
    if config_path is not None:
        paths_to_try.append(Path(config_path))
    paths_to_try.append(DEFAULT_CONFIG_PATH)

    # 加载第一个存在的配置文件
    for path in paths_to_try:
        if path.exists():
            raw = path.read_text(encoding="utf-8")
            raw = _resolve_env_vars(raw)
            file_data = yaml.safe_load(raw)
            if file_data and isinstance(file_data, dict):
                _apply_dict_to_config(file_data, config)
            break  # 只加载第一个找到的配置文件

    # 环境变量覆盖（仅 api_key 这种敏感字段）
    env_api_key = os.environ.get("DEEPSEEK_API_KEY")
    if env_api_key:
        config.deepseek.api_key = env_api_key

    return config


def _apply_dict_to_config(data: dict[str, Any], config: AppConfig) -> None:
    """将字典数据应用到 AppConfig 实例。"""
    for section_name, section_data in data.items():
        if not isinstance(section_data, dict):
            # 顶级字段（如 resume、max_retries、parallel_workers）
            if hasattr(config, section_name):
                old_value = getattr(config, section_name)
                value = section_data
                if isinstance(old_value, bool) and not isinstance(value, bool):
                    value = str(value).lower() in ("true", "1", "yes")
                elif isinstance(old_value, int) and not isinstance(value, int):
                    value = int(value)
                elif isinstance(old_value, float) and not isinstance(value, float):
                    value = float(value)
                setattr(config, section_name, value)
            continue
        section_obj = getattr(config, section_name, None)
        if section_obj is None:
            continue
        for key, value in section_data.items():
            if hasattr(section_obj, key):
                old_value = getattr(section_obj, key)
                if isinstance(old_value, bool) and not isinstance(value, bool):
                    value = str(value).lower() in ("true", "1", "yes")
                elif isinstance(old_value, int) and not isinstance(value, int):
                    value = int(value)
                elif isinstance(old_value, float) and not isinstance(value, float):
                    value = float(value)
                setattr(section_obj, key, value)
