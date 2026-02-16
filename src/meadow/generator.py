"""docstring generator for meadow.

with all my heart, 2025-2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module generates MDF-compliant docstrings from Python code elements.
"""

from pathlib import Path
from typing import TypedDict

from .config import Config, FormatConfig
from .validator import CodeElement, analyse_file


class UpdateResult(TypedDict):
    """result of updating docstrings in a file.

    attributes:
        `generated: int`
            number of new docstrings generated
        `updated: int`
            number of existing docstrings updated
        `skipped: int`
            number of docstrings skipped
        `malformed: int`
            number of malformed docstrings found
    """

    generated: int
    updated: int
    skipped: int
    malformed: int


class DocstringBuilder:
    """builds MDF docstrings from code elements.

    Combines generation and updating logic into a single builder class
    with a clear lifecycle.

    attributes:
        `config: FormatConfig`
            configuration for docstring formatting

    examples:
        ```python
        builder = DocstringBuilder(config)

        # Generate new docstring
        docstring = builder.build(element)

        # Update existing docstring
        docstring = builder.build(element, existing_docstring)
        ```
    """

    config: FormatConfig

    def __init__(self, config: FormatConfig | None = None) -> None:
        """initialise the builder

        arguments:
            `config: FormatConfig | None = None`
                format configuration

        returns: `none`
            no return value
        """
        self.config = config or FormatConfig()

    def build(
        self,
        element: CodeElement,
        existing_docstring: str | None = None,
    ) -> str:
        """build an mdf docstring for a code element

        arguments:
            `element: CodeElement`
                code element to document
            `existing_docstring: str | None = None`
                existing docstring to preserve preamble/body from

        returns: `str`
            generated mdf docstring
        """
        # extract existing content
        preamble = ""
        body: list[str] = []

        if existing_docstring:
            preamble, body = self._extract_existing_content(existing_docstring)

        # generate new docstring
        result_lines: list[str] = []

        # preamble
        result_lines.append(preamble or self._generate_preamble(element))

        # body
        if body:
            result_lines.append("")
            result_lines.extend(body)

        # arguments section
        if element.arguments:
            result_lines.append("")
            result_lines.extend(self._generate_arguments_section(element))

        # returns section (always generate, even for None)
        result_lines.append("")
        result_lines.extend(self._generate_returns_section(element))

        return self._format_docstring(result_lines)

    def _extract_existing_content(self, docstring: str) -> tuple[str, list[str]]:
        """extract preamble and body from existing docstring

        arguments:
            `docstring: str`
                existing docstring

        returns: `tuple[str, list[str]]`
            (preamble, body_lines)
        """
        lines = docstring.strip().split("\n")
        if not lines:
            return "", []

        preamble = ""
        body: list[str] = []

        # first non-empty line is preamble
        for line in lines:
            stripped = line.strip()
            if stripped:
                preamble = stripped
                break

        # remaining lines before any sections are body
        in_body = False
        for line in lines:
            stripped = line.strip()
            if stripped == preamble:
                in_body = True
                continue
            if in_body and not self._is_section_header(stripped):
                body.append(line)
            elif self._is_section_header(stripped):
                break

        return preamble, body

    def _generate_preamble(self, element: CodeElement) -> str:
        """generate a preamble for an element

        arguments:
            `element: CodeElement`
                element to generate preamble for

        returns: `str`
            generated preamble
        """
        name = element.name.split(".")[-1]

        match element.element_type:
            case "module":
                return f"module-level docstring for {name}"
            case "class":
                return f"a class representing {name}"
            case "function" | "method":
                return f"{name} implementation"
            case _:
                return f"documentation for {name}"

    def _is_section_header(self, line: str) -> bool:
        """check if a line is a section header

        arguments:
            `line: str`
                line to check

        returns: `bool`
            true if line is a section header
        """
        headers = [
            "attributes:",
            "arguments:",
            "parameters:",
            "functions:",
            "methods:",
            "returns:",
            "raises:",
            "usage:",
            "examples:",
        ]
        return line.lower().rstrip() in headers

    def _generate_arguments_section(self, element: CodeElement) -> list[str]:
        """generate arguments or parameters section

        arguments:
            `element: CodeElement`
                element with arguments

        returns: `list[str]`
            section lines
        """
        if not element.arguments:
            return []

        arg_lines: list[str] = []

        # choose section name
        section_name = "attributes:" if element.element_type == "class" else "arguments:"
        arg_lines.append(section_name)

        # generate entries
        indent = " " * self.config.indent_width

        for arg_name, type_ann, default in element.arguments:
            type_str = type_ann or "Any"
            if default:
                decl = f"`{arg_name}: {type_str} = {default}`"
            else:
                decl = f"`{arg_name}: {type_str}`"

            arg_lines.append(f"{indent}{decl}")
            arg_lines.append(f"{indent}{indent}description for {arg_name}")

        return arg_lines

    def _generate_returns_section(self, element: CodeElement) -> list[str]:
        """generate returns section

        arguments:
            `element: CodeElement`
                element with return annotation

        returns: `list[str]`
            section lines
        """
        ret_lines: list[str] = []
        indent = " " * self.config.indent_width

        # Always generate returns section, even for None
        if element.return_annotation:
            ret_lines.append(f"returns: `{element.return_annotation}`")
        else:
            ret_lines.append("returns: `none`")
        ret_lines.append(f"{indent}description of return value")

        return ret_lines

    def _format_docstring(self, lines: list[str]) -> str:
        """format docstring lines with proper indentation

        arguments:
            `lines: list[str]`
                lines to format

        returns: `str`
            formatted docstring
        """
        content = "\n".join(lines)

        if self.config.multi_line_summary_on_line == 2 and not content.startswith("\n"):
            content = "\n" + content

        return content


class DocstringUpdater:
    """updates existing docstrings in source files.

    Orchestrates the process of analysing files, generating docstrings,
    and tracking what changes would be made.

    attributes:
        `config: Config`
            meadow configuration
        `builder: DocstringBuilder`
            builder for generating docstrings

    examples:
        ```python
        updater = DocstringUpdater(config)
        result = updater.update_file(Path("src/main.py"))

        print(f"Generated: {result['generated']}")
        print(f"Updated: {result['updated']}")
        ```
    """

    config: Config
    builder: DocstringBuilder

    def __init__(self, config: Config) -> None:
        """initialise the updater

        arguments:
            `config: Config`
                configuration

        returns: `none`
            no return value
        """
        self.config = config
        self.builder = DocstringBuilder(config.format)

    def update_file(self, file_path: Path, fix_malformed: bool = False) -> UpdateResult:
        """update docstrings in a file

        arguments:
            `file_path: Path`
                path to python file
            `fix_malformed: bool = False`
                whether to fix malformed docstrings

        returns: `UpdateResult`
            summary of changes
        """
        result: UpdateResult = {
            "generated": 0,
            "updated": 0,
            "skipped": 0,
            "malformed": 0,
        }

        elements = analyse_file(file_path)
        if elements is None:
            return result

        for element in elements:
            if not self._should_document(element):
                continue

            if element.docstring is None:
                # generate new docstring
                _ = self.builder.build(element)
                result["generated"] += 1
            elif fix_malformed:
                # update existing
                _ = self.builder.build(element, element.docstring)
                result["updated"] += 1
            else:
                result["skipped"] += 1

        return result

    def _should_document(self, element: CodeElement) -> bool:
        """check if an element should be documented

        arguments:
            `element: CodeElement`
                element to check

        returns: `bool`
            true if element should be documented
        """
        name = element.name.split(".")[-1]

        # skip private elements
        if name.startswith("_") and not name.startswith("__"):
            return False

        # skip module docstrings if disabled
        if element.element_type == "module":
            return self.config.module_docstrings

        return True
