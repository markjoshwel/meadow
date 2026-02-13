"""tests for meadow config module
with all my heart, 2024-2025, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""

from pathlib import Path

from meadow.config import Config, FormatConfig, GenerateConfig


class TestConfig:
    """test suite for Config class"""

    def test_default_config(self) -> None:
        """Test default configuration values"""
        config = Config.default()

        assert isinstance(config.include, list)
        assert isinstance(config.exclude, list)
        assert config.respect_gitignore is True
        assert config.multi_line_summary_on_line in (1, 2)

    def test_format_config_defaults(self) -> None:
        """Test format config defaults"""
        fmt = FormatConfig()

        assert fmt.module_docstrings is False
        assert fmt.line_length == 79
        assert fmt.indent_width == 4
        assert fmt.indent_style == "space"
        assert fmt.multi_line_summary_on_line in (1, 2)

    def test_generate_config_defaults(self) -> None:
        """Test generate config defaults"""
        gen = GenerateConfig()

        assert gen.line_length == 79
        assert gen.indent_width == 4
        assert gen.indent_style == "space"
        assert isinstance(gen.external_links, dict)

    def test_config_to_example_toml(self) -> None:
        """Test generating example toml"""
        config = Config.default()
        toml = config.to_example_toml("meadoc")

        assert "[meadoc]" in toml
        assert "include" in toml
        assert "exclude" in toml
        assert "[meadoc.format]" in toml
        assert "[meadoc.generate]" in toml

    def test_config_to_example_toml_pyproject(self) -> None:
        """Test generating pyproject.toml example"""
        config = Config.default()
        toml = config.to_example_toml("tool.meadoc")

        assert "[tool.meadoc]" in toml
        assert "[tool.meadoc.format]" in toml


class TestConfigLoading:
    """test suite for config loading"""

    def test_load_returns_config(self, tmp_path: Path) -> None:
        """Test that load returns a Config object"""
        config = Config.load(tmp_path)
        assert isinstance(config, Config)

    def test_load_with_no_config_files(self, tmp_path: Path) -> None:
        """Test loading when no config files exist"""
        config = Config.load(tmp_path)
        # should return defaults
        assert len(config.exclude) > 0
