"""markdown API documentation generator for meadow.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module generates markdown API reference documentation from MDF docstrings.
"""

from __future__ import annotations

from pathlib import Path
from typing import NewType

from meadow.config import GenerateConfig
from meadow.parser import (
    ExceptionDoc,
    FunctionDoc,
    ParameterDoc,
    ReturnDoc,
    SectionType,
)
from meadow.validator import CodeElement, analyse_file

# type alias for markdown content
Markdown = NewType("Markdown", str)


class MarkdownGenerator:
    """generates markdown API documentation from code elements.

    Creates markdown-formatted API reference documentation from
    meadow-compliant docstrings.

    examples:
        ```python
        generator = MarkdownGenerator(config)
        markdown = generator.generate_for_file(Path("src/main.py"))
        ```
    """

    config: GenerateConfig

    def __init__(self, config: GenerateConfig | None = None) -> None:
        """Initialise the generator.

        arguments:
            `config: GenerateConfig | None = None`
                generate configuration

        returns: `none`
            no return value
        """
        self.config = config or GenerateConfig()

    def generate_for_file(
        self, file_path: Path, base_path: Path | None = None
    ) -> Markdown:
        """Generate markdown documentation for a Python file.

        arguments:
            `file_path: Path`
                path to Python file
            `base_path: Path | None = None`
                base path for relative links

        returns: `Markdown`
            generated markdown content
        """
        elements = analyse_file(file_path)
        if elements is None:
            return Markdown("")

        # collect all element markdown first to check if file has content
        module_name = self._get_module_name(file_path)
        element_sections: list[str] = []

        for element in elements:
            element_md = self._generate_for_element(element)
            if element_md:
                element_sections.append(element_md)

        # skip empty files
        if not element_sections:
            return Markdown("")

        # build output
        base_level = self.config.starting_header_level
        lines: list[str] = []
        lines.append(f"{'#' * (base_level + 1)} {module_name}")

        for section in element_sections:
            lines.append("")
            lines.append(section)

        return Markdown("\n".join(lines))

    def generate_for_files(
        self,
        file_paths: list[Path],
        base_path: Path | None = None,
        title: str = "api reference",
    ) -> Markdown:
        """Generate markdown documentation for multiple files.

        arguments:
            `file_paths: list[Path]`
                list of paths to Python files
            `base_path: Path | None = None`
                base path for relative links
            `title: str = "api reference"`
                document title

        returns: `Markdown`
            generated markdown content
        """
        base_level = self.config.starting_header_level
        lines: list[str] = []
        lines.append(f"{'#' * base_level} {title}")

        # collect all file outputs first
        file_outputs: list[tuple[str, str]] = []  # (module_name, content)
        toc_entries: list[str] = []

        for file_path in file_paths:
            module_name = self._get_module_name(file_path)
            file_md = self.generate_for_file(file_path, base_path)
            if file_md and file_md.strip():
                file_outputs.append((module_name, str(file_md)))
                # add TOC entry
                anchor = (
                    module_name.lower().replace(".", "-").replace(" ", "-")
                )
                toc_entries.append(f"- [{module_name}](#{anchor})")

        # if no files had content, return empty
        if not file_outputs:
            return Markdown("")

        # add TOC if enabled
        if self.config.include_toc and toc_entries:
            lines.append("")
            lines.append("## table of contents")
            lines.append("")
            lines.extend(toc_entries)

        # add file contents
        for _module_name, file_md in file_outputs:
            lines.append("")
            lines.append(file_md)

        return Markdown("\n".join(lines))

    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path.

        arguments:
            `file_path: Path`
                path to Python file

        returns: `str`
            module name (e.g., "package.module")
        """
        # try to construct module name from path
        parts: list[str] = []
        current = file_path

        # walk up until we find src or the root
        while current.name and current.name not in ("src", "."):
            if current.suffix == ".py":
                parts.append(current.stem)
            else:
                parts.append(current.name)
            current = current.parent

        # reverse to get correct order
        parts.reverse()

        # join with dots
        return ".".join(parts) if parts else file_path.stem

    def _generate_for_element(self, element: CodeElement) -> str:
        """Generate markdown for a single code element.

        arguments:
            `element: CodeElement`
                element to document

        returns: `str`
            markdown content
        """
        if not element.docstring:
            return ""

        from meadow.parser import MDFParser

        parser = MDFParser()
        parsed = parser.parse(element.docstring, element.line_number)

        if not parsed.is_mdf:
            return ""

        lines: list[str] = []

        # skip modules
        if element.element_type == "module":
            return ""

        # generate header (truncated)
        header_level = self._get_header_level(element.element_type)
        header = self._build_truncated_header(element)
        lines.append(f"{'#' * header_level} {header}")

        # preamble
        if parsed.preamble:
            lines.append("")
            lines.append(parsed.preamble)

        # signature block for functions/methods
        if element.element_type in ("function", "method"):
            sig = self._build_full_signature(element)
            if sig:
                lines.append("")
                lines.append("- signature:")
                lines.append("")
                lines.append("  ```python")
                lines.append(f"  {sig}")
                lines.append("  ```")

        # body - filter out empty strings
        body_content = [line for line in parsed.body if line.strip()]
        if body_content:
            lines.append("")
            lines.extend(body_content)

        # attributes/arguments
        args_section = None
        args_section_type = SectionType.ARGUMENTS
        for section_type in (
            SectionType.ATTRIBUTES,
            SectionType.ARGUMENTS,
            SectionType.PARAMETERS,
        ):
            section = parsed.get_section(section_type)
            if section:
                args_section = section
                args_section_type = section_type
                break

        if args_section and args_section.items:
            lines.append("")
            lines.append(self._format_section_header(args_section_type))
            lines.append("")

            for item in args_section.items:
                if isinstance(item, ParameterDoc):
                    lines.extend(self._format_parameter(item))

        # methods/functions
        funcs_section = None
        funcs_section_type = SectionType.FUNCTIONS
        for section_type in (SectionType.FUNCTIONS, SectionType.METHODS):
            section = parsed.get_section(section_type)
            if section:
                funcs_section = section
                funcs_section_type = section_type
                break

        if funcs_section and funcs_section.items:
            lines.append("")
            lines.append(self._format_section_header(funcs_section_type))
            lines.append("")

            for item in funcs_section.items:
                if isinstance(item, FunctionDoc):
                    lines.extend(self._format_function(item))

        # returns
        returns_section = parsed.get_section(SectionType.RETURNS)
        if returns_section and returns_section.items:
            lines.append("")
            lines.append(self._format_section_header(SectionType.RETURNS))
            lines.append("")

            for item in returns_section.items:
                if isinstance(item, ReturnDoc):
                    lines.extend(self._format_return(item))

        # raises
        raises_section = parsed.get_section(SectionType.RAISES)
        if raises_section and raises_section.items:
            lines.append("")
            lines.append(self._format_section_header(SectionType.RAISES))
            lines.append("")

            for item in raises_section.items:
                if isinstance(item, ExceptionDoc):
                    lines.extend(self._format_exception(item))

        return "\n".join(lines)

    def _build_truncated_header(self, element: CodeElement) -> str:
        """Build truncated header text for an element.

        arguments:
            `element: CodeElement`
                element to build header for

        returns: `str`
            truncated header (e.g., "def name()" or "class Name")
        """
        if element.element_type == "class":
            # classes don't have ()
            return f"class {element.name}"
        else:
            # function or method - truncated to def name()
            return f"def {element.name}()"

    def _build_full_signature(self, element: CodeElement) -> str:
        """Build full signature string for a function/method.

        arguments:
            `element: CodeElement`
                element to build signature for

        returns: `str`
            full signature string
        """
        args_str = ""
        if element.arguments:
            arg_parts: list[str] = []
            for arg_name, type_ann, default in element.arguments:
                if type_ann and default:
                    arg_parts.append(f"{arg_name}: {type_ann} = {default}")
                elif type_ann:
                    arg_parts.append(f"{arg_name}: {type_ann}")
                elif default:
                    arg_parts.append(f"{arg_name} = {default}")
                else:
                    arg_parts.append(arg_name)
            args_str = ", ".join(arg_parts)

        return_annotation = ""
        if element.return_annotation:
            return_annotation = f" -> {element.return_annotation}"

        return f"def {element.name}({args_str}){return_annotation}:"

    def _get_header_level(self, element_type: str) -> int:
        """Get markdown header level for element type.

        arguments:
            `element_type: str`
                type of element

        returns: `int`
            header level (number of # characters)
        """
        base = self.config.starting_header_level
        offsets = {
            "module": 1,  # h3 (base=2)
            "class": 2,  # h4 (base=2)
            "function": 2,  # h4 (base=2)
            "method": 3,  # h5 (base=2)
        }
        return base + offsets.get(element_type, 2)

    def _format_section_header(self, section_type: SectionType) -> str:
        """Format a section header.

        arguments:
            `section_type: SectionType`
                section type

        returns: `str`
            formatted header
        """
        names = {
            SectionType.ATTRIBUTES: "attributes",
            SectionType.ARGUMENTS: "arguments",
            SectionType.PARAMETERS: "parameters",
            SectionType.FUNCTIONS: "functions",
            SectionType.METHODS: "methods",
            SectionType.RETURNS: "returns",
            SectionType.RAISES: "raises",
            SectionType.USAGE: "usage",
        }

        return f"- {names.get(section_type, str(section_type))}:"

    def _format_parameter(self, param: ParameterDoc) -> list[str]:
        """Format a parameter documentation.

        arguments:
            `param: ParameterDoc`
                parameter documentation

        returns: `list[str]`
            formatted lines
        """
        lines: list[str] = []
        type_str = param.type_annotation or "Any"

        if param.default_value:
            first_line = (
                f"  - `{param.name}: {type_str} = {param.default_value}`"
            )
        else:
            first_line = f"  - `{param.name}: {type_str}`"

        if param.description:
            first_line += "  "  # two spaces for markdown line break
            lines.append(first_line)
            desc = " ".join(param.description)
            lines.append(f"    {desc}")
        else:
            lines.append(first_line)

        return lines

    def _format_function(self, func: FunctionDoc) -> list[str]:
        """Format a function documentation.

        arguments:
            `func: FunctionDoc`
                function documentation

        returns: `list[str]`
            formatted lines
        """
        lines: list[str] = []
        first_line = f"  - `{func.signature}`"

        if func.description:
            first_line += "  "  # two spaces for markdown line break
            lines.append(first_line)
            desc = " ".join(func.description)
            lines.append(f"    {desc}")
        else:
            lines.append(first_line)

        return lines

    def _format_return(self, ret: ReturnDoc) -> list[str]:
        """Format a return documentation.

        arguments:
            `ret: ReturnDoc`
                return documentation

        returns: `list[str]`
            formatted lines
        """
        lines: list[str] = []
        type_str = ret.type_annotation or "Any"
        first_line = f"  - `{type_str}`"

        if ret.description:
            first_line += "  "  # two spaces for markdown line break
            lines.append(first_line)
            desc = " ".join(ret.description)
            lines.append(f"    {desc}")
        else:
            lines.append(first_line)

        return lines

    def _format_exception(self, exc: ExceptionDoc) -> list[str]:
        """Format an exception documentation.

        arguments:
            `exc: ExceptionDoc`
                exception documentation

        returns: `list[str]`
            formatted lines
        """
        lines: list[str] = []
        first_line = f"  - `{exc.exception_class}`"

        if exc.description:
            first_line += "  "  # two spaces for markdown line break
            lines.append(first_line)
            desc = " ".join(exc.description)
            lines.append(f"    {desc}")
        else:
            lines.append(first_line)

        return lines
