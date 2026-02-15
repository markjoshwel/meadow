"""configuration loading and management for meadow.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module handles loading configuration from pyproject.toml, meadoc.toml,
and .meadoc.toml files, as well as command-line argument processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.items import Table

from meadow.errors import ConfigError, Location

# constants
DEFAULT_INCLUDE_PATTERNS: list[str] = [
    "src/**/*.py",
    "tests/**/*.py",
]

DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pyenv",
    ".pytest_cache",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
]

CONFIG_SEARCH_ORDER: list[str] = [
    ".meadoc.toml",
    "meadoc.toml",
    "pyproject.toml",
]

SUMMARY_LINE_OPTIONS: tuple[int, ...] = (1, 2)
INDENT_STYLE_OPTIONS: tuple[str, ...] = ("space", "tab")


def _get_bool(table: Table, key: str) -> bool | None:
    """safely get a boolean value from a TOML table.

    arguments:
        `table: Table`
            the TOML table to read from
        `key: str`
            the key to look up

    returns: `bool | None`
        the boolean value if present and valid, None otherwise
    """
    value: object = table.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if isinstance(value, bool):
        return value
    return None


def _get_int(table: Table, key: str) -> int | None:
    """safely get an integer value from a TOML table.

    arguments:
        `table: Table`
            the TOML table to read from
        `key: str`
            the key to look up

    returns: `int | None`
        the integer value if present and valid, None otherwise
    """
    value: object = table.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if isinstance(value, int):
        return value
    return None


def _get_str(table: Table, key: str) -> str | None:
    """safely get a string value from a TOML table.

    arguments:
        `table: Table`
            the TOML table to read from
        `key: str`
            the key to look up

    returns: `str | None`
        the string value if present and valid, None otherwise
    """
    value: object = table.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if isinstance(value, str):
        return value
    return None


def _get_list(table: Table, key: str) -> list[object] | None:
    """safely get a list value from a TOML table.

    arguments:
        `table: Table`
            the TOML table to read from
        `key: str`
            the key to look up

    returns: `list[object] | None`
        the list value if present and valid, None otherwise
    """
    value: object = table.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if isinstance(value, list):
        return cast(list[object], value)
    return None


def _get_table(table: Table | TOMLDocument, key: str) -> Table | None:
    """safely get a table value from a TOML table or document.

    arguments:
        `table: Table | TOMLDocument`
            the TOML table or document to read from
        `key: str`
            the key to look up

    returns: `Table | None`
        the table value if present and valid, None otherwise
    """
    value: object = table.get(key)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if isinstance(value, Table):
        return value
    return None


@dataclass
class FormatConfig:
    """configuration for the format subcommand.

    Controls how docstrings are formatted and generated.

    attributes:
        `line_length: int = 79`
            maximum line length for docstrings
        `line_ending: str = ""`
            line ending to use (empty = autodetect)
        `indent_width: int = 4`
            number of spaces/tabs for indentation
        `indent_style: Literal["space", "tab"] = "space"`
            whether to use spaces or tabs
        `code_block_format: bool = True`
            whether to format code blocks
        `code_block_format_command: list[str]`
            command to format code blocks
        `multi_line_summary_on_line: Literal[1, 2] = 2`
            which line to place multi-line summary on
    """

    line_length: int = 79
    line_ending: str = ""  # empty = autodetect
    indent_width: int = 4
    indent_style: Literal["space", "tab"] = "space"
    code_block_format: bool = True
    code_block_format_command: list[str] = field(
        default_factory=lambda: ["ruff", "format", "-"]
    )
    multi_line_summary_on_line: Literal[1, 2] = 2


@dataclass
class GenerateConfig:
    """configuration for the generate subcommand.

    Controls how markdown API documentation is generated.

    attributes:
        `external_link_reference: str = "meadoc.toml"`
            file to store external link definitions
        `line_length: int = 79`
            maximum line length for markdown output
        `line_ending: str = ""`
            line ending to use (empty = autodetect)
        `indent_width: int = 4`
            number of spaces/tabs for indentation
        `indent_style: Literal["space", "tab"] = "space"`
            whether to use spaces or tabs
        `external_links: dict[str, str]`
            mapping of type names to documentation URLs
        `starting_header_level: Literal[1, 2, 3, 4, 5, 6] = 2`
            starting header level for api reference title
        `include_toc: bool = True`
            whether to include table of contents
    """

    external_link_reference: str = "meadoc.toml"
    line_length: int = 79
    line_ending: str = ""  # empty = autodetect
    indent_width: int = 4
    indent_style: Literal["space", "tab"] = "space"
    external_links: dict[str, str] = field(default_factory=dict)
    starting_header_level: Literal[1, 2, 3, 4, 5, 6] = 2
    include_toc: bool = True


@dataclass
class Config:
    """complete meadow configuration.

    Aggregates all configuration options for the meadoc tool.

    attributes:
        `include: list[str]`
            glob patterns for files to include
        `exclude: list[str]`
            glob patterns for files to exclude
        `respect_gitignore: bool = True`
            whether to respect .gitignore files
        `multi_line_summary_on_line: Literal[1, 2] = 2`
            which line to place multi-line summary on
        `module_docstrings: bool = False`
            whether to process module-level docstrings
        `format: FormatConfig`
            format subcommand configuration
        `generate: GenerateConfig`
            generate subcommand configuration

    examples:
        ```python
        # Load from default locations
        config = Config.load()

        # Create with defaults
        config = Config.default()

        # Access settings
        print(config.format.line_length)
        ```
    """

    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    respect_gitignore: bool = True
    multi_line_summary_on_line: Literal[1, 2] = 2
    module_docstrings: bool = False
    format: FormatConfig = field(default_factory=FormatConfig)
    generate: GenerateConfig = field(default_factory=GenerateConfig)

    @classmethod
    def default(cls) -> Config:
        """create a configuration with default values

        returns: `Config`
            configuration populated with default values
        """
        return cls(
            include=list(DEFAULT_INCLUDE_PATTERNS),
            exclude=list(DEFAULT_EXCLUDE_PATTERNS),
            respect_gitignore=True,
            multi_line_summary_on_line=2,
            format=FormatConfig(),
            generate=GenerateConfig(),
        )

    @classmethod
    def load(cls, start_path: Path | None = None) -> Config:
        """load configuration from available config files

        searches for configuration files in order of precedence:
        1. .meadoc.toml
        2. meadoc.toml
        3. pyproject.toml

        arguments:
            `start_path: Path | None = None`
                directory to start searching from (defaults to cwd)

        returns: `Config`
            loaded configuration with defaults applied

        raises:
            `ConfigError`
                if a config file exists but cannot be parsed
        """
        config = cls.default()

        if start_path is None:
            start_path = Path.cwd()

        # search for config files in order of precedence
        for filename in CONFIG_SEARCH_ORDER:
            config_path = start_path / filename
            if config_path.exists():
                try:
                    config._load_from_file(config_path)
                    return config
                except Exception as exc:
                    raise ConfigError(
                        message=f"Failed to parse {filename}: {exc}",
                        location=Location(
                            line=1,
                            column=0,
                            file=str(config_path),
                        ),
                    ) from exc

        return config

    def _load_from_file(self, path: Path) -> None:
        """load configuration from a toml file

        arguments:
            `path: Path`
                path to the configuration file

        returns: `none`

        raises:
            `ConfigError`
                if the file cannot be read or contains invalid values
        """
        try:
            content = path.read_text(encoding="utf-8")
            doc: TOMLDocument = tomlkit.parse(content)
        except OSError as exc:
            raise ConfigError(
                message=f"Cannot read config file: {exc}",
                location=Location(line=1, column=0, file=str(path)),
            ) from exc

        # determine the config table based on file type
        config_table: Table | None = None

        if path.name == "pyproject.toml":
            tool_table = _get_table(doc, "tool")
            if tool_table:
                config_table = _get_table(tool_table, "meadoc")
        else:
            config_table = _get_table(doc, "meadoc")

        if config_table is None:
            return

        # load top-level options
        include_value = _get_list(config_table, "include")
        if include_value:
            self.include = [str(item) for item in include_value]

        exclude_value = _get_list(config_table, "exclude")
        if exclude_value:
            self.exclude = [str(item) for item in exclude_value]

        respect_value = _get_bool(config_table, "respect-gitignore")
        if respect_value is not None:
            self.respect_gitignore = respect_value

        summary_value = _get_int(config_table, "multi-line-summary-on-line")
        if summary_value is not None and summary_value in SUMMARY_LINE_OPTIONS:
            self.multi_line_summary_on_line = cast(
                Literal[1, 2], summary_value
            )

        module_docstrings = _get_bool(config_table, "module-docstrings")
        if module_docstrings is not None:
            self.module_docstrings = module_docstrings

        # load format section
        format_table = _get_table(config_table, "format")
        if format_table:
            self._load_format_config(format_table)

        # load generate section
        generate_table = _get_table(config_table, "generate")
        if generate_table:
            self._load_generate_config(generate_table)

    def _load_format_config(self, table: Table) -> None:
        """load format configuration from a toml table

        arguments:
            `table: Table`
                the [meadoc.format] or [tool.meadoc.format] table

        returns: `none`
            no return value
        """
        line_length = _get_int(table, "line-length")
        if line_length is not None and line_length > 0:
            self.format.line_length = line_length

        line_ending = _get_str(table, "line-ending")
        if line_ending is not None:
            self.format.line_ending = line_ending

        indent_width = _get_int(table, "indent-width")
        if indent_width is not None and indent_width > 0:
            self.format.indent_width = indent_width

        indent_style = _get_str(table, "indent-style")
        if indent_style is not None and indent_style in INDENT_STYLE_OPTIONS:
            self.format.indent_style = cast(
                Literal["space", "tab"], indent_style
            )

        code_block_format = _get_bool(table, "code-block-format")
        if code_block_format is not None:
            self.format.code_block_format = code_block_format

        code_block_command = _get_list(table, "code-block-format-command")
        if code_block_command:
            self.format.code_block_format_command = [
                str(item) for item in code_block_command
            ]

        summary_line = _get_int(table, "multi-line-summary-on-line")
        if summary_line is not None and summary_line in SUMMARY_LINE_OPTIONS:
            self.format.multi_line_summary_on_line = cast(
                Literal[1, 2], summary_line
            )

    def _load_generate_config(self, table: Table) -> None:
        """load generate configuration from a toml table

        arguments:
            `table: Table`
                the [meadoc.generate] or [tool.meadoc.generate] table

        returns: `none`
            no return value
        """
        external_link_ref = _get_str(table, "external-link-reference")
        if external_link_ref is not None:
            self.generate.external_link_reference = external_link_ref

        line_length = _get_int(table, "line-length")
        if line_length is not None and line_length > 0:
            self.generate.line_length = line_length

        line_ending = _get_str(table, "line-ending")
        if line_ending is not None:
            self.generate.line_ending = line_ending

        indent_width = _get_int(table, "indent-width")
        if indent_width is not None and indent_width > 0:
            self.generate.indent_width = indent_width

        indent_style = _get_str(table, "indent-style")
        if indent_style is not None and indent_style in INDENT_STYLE_OPTIONS:
            self.generate.indent_style = cast(
                Literal["space", "tab"], indent_style
            )

        external_links = _get_table(table, "external-links")
        if external_links:
            links_dict: dict[str, str] = {}
            for key_obj, value_obj in external_links.items():  # pyright: ignore[reportUnknownVariableType]
                key: object = key_obj  # pyright: ignore[reportUnknownVariableType]
                value: object = value_obj  # pyright: ignore[reportUnknownVariableType]
                links_dict[str(cast(object, key))] = str(cast(object, value))
            self.generate.external_links = links_dict

    def to_example_toml(self, table_name: str = "meadoc") -> str:
        """generate example toml configuration as a string

        arguments:
            `table_name: str = "meadoc"`
                the table name to use ("meadoc" or "tool.meadoc")

        returns: `str`
            formatted toml configuration
        """
        lines: list[str] = [
            f"# example {table_name}.toml configuration",
            "",
            f"[{table_name}]",
            "# source file resolution",
            "# glob patterns to include/exclude/ignore files and directories",
            "include = [",
        ]

        for pattern in self.include:
            lines.append(f'    "{pattern}",')
        lines.append("]")

        lines.append("exclude = [")
        for pattern in self.exclude:
            lines.append(f'    "{pattern}",')
        lines.append("]")

        lines.extend(
            [
                "",
                "# meadoc will by default respect .gitignores",
                f"respect-gitignore = {str(self.respect_gitignore).lower()}",
                "",
                f"multi-line-summary-on-line = {self.multi_line_summary_on_line}",
                "",
                "# module docstrings usually have more varied styling/writing,",
                "# so it is disabled by default",
                f"module-docstrings = {str(self.module_docstrings).lower()}",
                "",
                f"[{table_name}.format]",
                "# docstring formatting preferences",
                f"line-length = {self.format.line_length}",
                f'line-ending = "{self.format.line_ending}"',
                f"indent-width = {self.format.indent_width}",
                f'indent-style = "{self.format.indent_style}"',
                "",
                "# any detected python code blocks can be formatted",
                f"code-block-format = {str(self.format.code_block_format).lower()}",
                "code-block-format-command = [",
            ]
        )

        for cmd in self.format.code_block_format_command:
            lines.append(f'    "{cmd}",')
        lines.append("]")

        lines.extend(
            [
                "",
                f"[{table_name}.generate]",
                f'external-link-reference = "{self.generate.external_link_reference}"',
                "",
                "# markdown formatting preferences",
                f"line-length = {self.generate.line_length}",
                f'line-ending = "{self.generate.line_ending}"',
                f"indent-width = {self.generate.indent_width}",
                f'indent-style = "{self.generate.indent_style}"',
                "",
            ]
        )

        if self.generate.external_links:
            lines.append(f"[{table_name}.generate.external-links]")
            for key, value in self.generate.external_links.items():
                lines.append(f'{key} = "{value}"')
            lines.append("")

        return "\n".join(lines)


def find_project_root(start_path: Path | None = None) -> Path:
    """find the project root directory

    searches for common project indicators like .git, pyproject.toml,
    and meadoc.toml files

    arguments:
        `start_path: Path | None = None`
            directory to start searching from (defaults to cwd)

    returns: `Path`
        the project root directory, or start_path if none found
    """
    if start_path is None:
        start_path = Path.cwd()

    indicators = [
        ".git",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        ".meadoc.toml",
        "meadoc.toml",
    ]

    for parent in [start_path, *start_path.parents]:
        for indicator in indicators:
            if (parent / indicator).exists():
                return parent

    return start_path
