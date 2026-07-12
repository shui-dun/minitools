"""config.py 单元测试。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from bookwhisper.config import AppConfig, DeepSeekConfig, load_config


class TestAppConfigDefaults:
    """默认值测试。"""

    def test_default_config(self) -> None:
        config = AppConfig()
        assert config.deepseek.model == "deepseek-v4-pro"
        assert config.deepseek.temperature == 0.3
        assert config.chunk.max_chars == 15000
        assert config.chunk.book_summary_chars == 800
        assert config.output.dir == "./output"
        assert config.output.suffix == "_interpreted"
        assert config.resume is True
        assert config.max_retries == 3

    def test_nested_config_types(self) -> None:
        config = AppConfig()
        assert isinstance(config.deepseek, DeepSeekConfig)
        assert isinstance(config.chunk.max_chars, int)
        assert isinstance(config.deepseek.temperature, float)


class TestApplyCliOverrides:
    """CLI 参数覆盖测试。"""

    def test_override_string(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({"deepseek.model": "deepseek-reasoner"})
        assert config.deepseek.model == "deepseek-reasoner"

    def test_override_int(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({"chunk.max_chars": "2000"})
        assert config.chunk.max_chars == 2000

    def test_override_float(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({"deepseek.temperature": "0.8"})
        assert config.deepseek.temperature == 0.8

    def test_override_multiple(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({
            "deepseek.model": "deepseek-v4-pro",
            "chunk.max_chars": "1500",
            "output.dir": "/tmp/out",
        })
        assert config.deepseek.model == "deepseek-v4-pro"
        assert config.chunk.max_chars == 1500
        assert config.output.dir == "/tmp/out"

    def test_override_invalid_key_ignored(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({"nonexistent.field": "value"})
        # 不应该报错

    def test_override_bool_true(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({"resume": "true"})
        assert config.resume is True

    def test_override_bool_false(self) -> None:
        config = AppConfig()
        config.apply_cli_overrides({"resume": "false"})
        assert config.resume is False


class TestAsNestedDict:
    """嵌套字典导"""

    def test_as_nested_dict(self) -> None:
        config = AppConfig()
        d = config.as_nested_dict()
        assert "deepseek" in d
        assert d["deepseek"]["model"] == "deepseek-v4-pro"
        assert d["chunk"]["max_chars"] == 15000
        assert d["output"]["dir"] == "./output"


class TestLoadConfigFromYaml:
    """YAML 配置加载测试。"""

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "config.yaml"
        yaml_path.write_text("""
deepseek:
  model: "deepseek-reasoner"
  temperature: 0.5
chunk:
  max_chars: 2000
output:
  dir: "./my_output"
""", encoding="utf-8")

        config = load_config(yaml_path)
        assert config.deepseek.model == "deepseek-reasoner"
        assert config.deepseek.temperature == 0.5
        assert config.chunk.max_chars == 2000
        assert config.output.dir == "./my_output"

    def test_load_env_var_interpolation(self, tmp_path: Path) -> None:
        os.environ["TEST_API_KEY"] = "sk-test-12345"
        # 避免真实 DEEPSEEK_API_KEY 干扰测试
        old_deepseek_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            yaml_path = tmp_path / "config.yaml"
            yaml_path.write_text("""
deepseek:
  api_key: "${TEST_API_KEY}"
""", encoding="utf-8")

            config = load_config(yaml_path)
            assert config.deepseek.api_key == "sk-test-12345"
        finally:
            del os.environ["TEST_API_KEY"]
            if old_deepseek_key:
                os.environ["DEEPSEEK_API_KEY"] = old_deepseek_key

    def test_env_var_override(self) -> None:
        old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            os.environ["DEEPSEEK_API_KEY"] = "sk-env-override"
            config = load_config()
            assert config.deepseek.api_key == "sk-env-override"
        finally:
            del os.environ["DEEPSEEK_API_KEY"]
            if old_key:
                os.environ["DEEPSEEK_API_KEY"] = old_key

    def test_load_nonexistent_yaml(self) -> None:
        """不存在的 YAML 文件不应报错，使用默认值。"""
        config = load_config("/nonexistent/path.yaml")
        assert config.deepseek.model == "deepseek-v4-pro"
