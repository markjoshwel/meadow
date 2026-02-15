"""markdown API documentation generator for meadow.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module generates markdown API reference documentation from MDF docstrings.
"""


import ast
import sys
from pathlib import Path
from typing import NewType, cast

import tomlkit

from .config import GenerateConfig
from .parser import (
    ExceptionDoc,
    FunctionDoc,
    ParameterDoc,
    ReturnDoc,
    SectionType,
)
from .validator import CodeElement, analyse_file

# type alias for markdown content
Markdown = NewType("Markdown", str)

# standard library modules for external link auto-discovery
STDLIB_MODULES: frozenset[str] = frozenset(
    [
        *sys.builtin_module_names,
        # common stdlib modules that might be imported
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "base64",
        "bisect",
        "builtins",
        "calendar",
        "collections",
        "concurrent",
        "configparser",
        "contextlib",
        "copy",
        "csv",
        "ctypes",
        "dataclasses",
        "datetime",
        "decimal",
        "difflib",
        "dis",
        "enum",
        "fractions",
        "functools",
        "glob",
        "graphlib",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "idlelib",
        "imghdr",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "linecache",
        "locale",
        "logging",
        "mailbox",
        "math",
        "mimetypes",
        "mmap",
        "multiprocessing",
        "numbers",
        "operator",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "queue",
        "quopri",
        "random",
        "re",
        "reprlib",
        "resource",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "socket",
        "socketserver",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
    ]
)


class MarkdownGenerator:
    """generates markdown API documentation from code elements.

    Creates markdown-formatted API reference documentation from
    meadow-compliant docstrings.

    attributes:
        `config: GenerateConfig`
            configuration for markdown generation

    examples:
        ```python
        generator = MarkdownGenerator(config)
        markdown = generator.generate_for_file(Path("src/main.py"))
        ```
    """

    config: GenerateConfig

    def __init__(self, config: GenerateConfig | None = None) -> None:
        """initialise the generator

        arguments:
            `config: GenerateConfig | None = None`
                generate configuration

        returns: `none`
            no return value
        """
        self.config = config or GenerateConfig()

    def generate_for_file(
        self, file_path: Path, _base_path: Path | None = None
    ) -> Markdown:
        """generate markdown documentation for a python file

        arguments:
            `file_path: Path`
                path to python file
            `_base_path: Path | None = None`
                base path for relative links (unused)

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
        """generate markdown documentation for multiple files

        arguments:
            `file_paths: list[Path]`
                list of paths to python files
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
        for _module_name, content in file_outputs:
            lines.append("")
            lines.append(content)

        return Markdown("\n".join(lines))

    def _get_module_name(self, file_path: Path) -> str:
        """get module name from file path

        arguments:
            `file_path: Path`
                path to python file

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
        """generate markdown for a single code element

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
        """build truncated header text for an element

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
        """build full signature string for a function/method

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
        """get markdown header level for element type

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
        """format a section header

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
        """format a parameter documentation

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
        """format a function documentation

        for methods/functions sections, only show the function name
        without the full signature, as the full signature is shown
        in the actual function documentation

        arguments:
            `func: FunctionDoc`
                function documentation

        returns: `list[str]`
            formatted lines
        """
        lines: list[str] = []

        # extract just the function name from the signature
        # signature format: "def name(args) -> return_type"
        func_name = self._extract_function_name(func.signature)
        first_line = f"  - `def {func_name}()`"

        if func.description:
            first_line += "  "  # two spaces for markdown line break
            lines.append(first_line)
            desc = " ".join(func.description)
            lines.append(f"    {desc}")
        else:
            lines.append(first_line)

        return lines

    def _extract_function_name(self, signature: str) -> str:
        """extract the function name from a signature

        arguments:
            `signature: str`
                full function signature (e.g., "def foo(arg: int) -> str")

        returns: `str`
            function name only
        """
        # remove 'def ' prefix
        if signature.startswith("def "):
            signature = signature[4:]
        elif signature.startswith("async def "):
            signature = signature[10:]

        # extract name up to opening parenthesis
        if "(" in signature:
            return signature.split("(")[0].strip()

        # fallback: return as-is
        return signature.strip()

    def _format_return(self, ret: ReturnDoc) -> list[str]:
        """format a return documentation

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
        """format an exception documentation

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

    def collect_external_types(self, file_paths: list[Path]) -> set[str]:
        """collect all external type references from docstrings

        scans all files and collects type annotations that reference
        external modules (stdlib or third-party).

        arguments:
            `file_paths: list[Path]`
                list of python files to scan

        returns: `set[str]`
            set of fully qualified type names (e.g., "pathlib.Path")
        """
        external_types: set[str] = set()

        for file_path in file_paths:
            elements = analyse_file(file_path)
            if elements is None:
                continue

            for element in elements:
                if not element.docstring:
                    continue

                from meadow.parser import MDFParser

                parser = MDFParser()
                parsed = parser.parse(element.docstring, element.line_number)

                if not parsed.is_mdf:
                    continue

                # collect types from arguments/attributes
                for section_type in (
                    SectionType.ARGUMENTS,
                    SectionType.PARAMETERS,
                    SectionType.ATTRIBUTES,
                ):
                    section = parsed.get_section(section_type)
                    if section:
                        for item in section.items:
                            if isinstance(item, ParameterDoc):
                                if item.type_annotation:
                                    types = (
                                        self._extract_types_from_annotation(
                                            item.type_annotation
                                        )
                                    )
                                    external_types.update(types)

                # collect types from returns
                returns_section = parsed.get_section(SectionType.RETURNS)
                if returns_section:
                    for item in returns_section.items:
                        if isinstance(item, ReturnDoc):
                            if item.type_annotation:
                                types = self._extract_types_from_annotation(
                                    item.type_annotation
                                )
                                external_types.update(types)

                # collect types from raises
                raises_section = parsed.get_section(SectionType.RAISES)
                if raises_section:
                    for item in raises_section.items:
                        if isinstance(item, ExceptionDoc):
                            if "." in item.exception_class:
                                # already fully qualified
                                external_types.add(item.exception_class)
                            else:
                                # check if it's a stdlib exception
                                module = self._guess_exception_module(
                                    item.exception_class
                                )
                                if module:
                                    external_types.add(
                                        f"{module}.{item.exception_class}"
                                    )

        return external_types

    def _extract_types_from_annotation(self, annotation: str) -> set[str]:
        """extract external type references from a type annotation

        arguments:
            `annotation: str`
                type annotation string (e.g., "list[pathlib.Path] | None")

        returns: `set[str]`
            set of fully qualified type names
        """
        types: set[str] = set()

        # parse the annotation using ast
        try:
            tree = ast.parse(annotation, mode="eval")
        except SyntaxError:
            return types

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                # simple name like "Path" - can't determine module
                pass
            elif isinstance(node, ast.Attribute):
                # qualified name like "pathlib.Path"
                if isinstance(node.value, ast.Name):
                    module = node.value.id
                    type_name = node.attr
                    if module in STDLIB_MODULES:
                        types.add(f"{module}.{type_name}")
                    elif module not in ("self", "cls"):
                        # likely third-party
                        types.add(f"{module}.{type_name}")
            elif isinstance(node, ast.Subscript):
                # generic like "list[Path]" - handled by walking
                pass

        return types

    def _guess_exception_module(self, exc_name: str) -> str | None:
        """guess the module for an exception class

        arguments:
            `exc_name: str`
                exception class name

        returns: `str | None`
            module name if it's a known exception, None otherwise
        """
        # common stdlib exceptions
        builtins_exceptions = {
            "Exception",
            "BaseException",
            "ArithmeticError",
            "AssertionError",
            "AttributeError",
            "BlockingIOError",
            "BrokenPipeError",
            "BufferError",
            "BytesWarning",
            "ChildProcessError",
            "ConnectionAbortedError",
            "ConnectionError",
            "ConnectionRefusedError",
            "ConnectionResetError",
            "DeprecationWarning",
            "EOFError",
            "EnvironmentError",
            "FileExistsError",
            "FileNotFoundError",
            "FloatingPointError",
            "FutureWarning",
            "GeneratorExit",
            "IOError",
            "ImportError",
            "ImportWarning",
            "IndentationError",
            "IndexError",
            "InterruptedError",
            "IsADirectoryError",
            "KeyError",
            "KeyboardInterrupt",
            "LookupError",
            "MemoryError",
            "ModuleNotFoundError",
            "NameError",
            "NotADirectoryError",
            "NotImplementedError",
            "OSError",
            "OverflowError",
            "PendingDeprecationWarning",
            "PermissionError",
            "ProcessLookupError",
            "RecursionError",
            "ReferenceError",
            "ResourceWarning",
            "RuntimeError",
            "RuntimeWarning",
            "StopAsyncIteration",
            "StopIteration",
            "SyntaxError",
            "SyntaxWarning",
            "SystemError",
            "SystemExit",
            "TabError",
            "TimeoutError",
            "TypeError",
            "UnboundLocalError",
            "UnicodeDecodeError",
            "UnicodeEncodeError",
            "UnicodeError",
            "UnicodeTranslateError",
            "UnicodeWarning",
            "UserWarning",
            "ValueError",
            "Warning",
            "ZeroDivisionError",
        }

        if exc_name in builtins_exceptions:
            return "builtins"

        return None

    def update_external_links(
        self,
        external_types: set[str],
        project_root: Path,
    ) -> None:
        """update external links file with newly discovered types

        adds any types not already present in the external links
        configuration to the external link reference file.

        arguments:
            `external_types: set[str]`
                set of external type names to add
            `project_root: Path`
                project root for finding the config file

        returns: `none`
            no return value
        """
        if not external_types:
            return

        # determine which file to update
        link_ref_file = self.config.external_link_reference
        config_path = project_root / link_ref_file

        # load existing config from file if it exists
        existing_links: dict[str, str] = {}
        doc = tomlkit.document()

        if config_path.exists():
            try:
                content = config_path.read_text(encoding="utf-8")
                parsed_doc = tomlkit.parse(content)
                if parsed_doc is not None:  # type: ignore
                    # get existing external links
                    meadoc_table = parsed_doc.get("meadoc")
                    if isinstance(meadoc_table, dict):
                        generate_table = meadoc_table.get("generate")
                        if isinstance(generate_table, dict):
                            links_table = generate_table.get("external-links")
                            if isinstance(links_table, dict):
                                for k_obj, v_obj in links_table.items():  # type: ignore
                                    existing_links[
                                        str(cast(object, k_obj))
                                    ] = str(cast(object, v_obj))
                        # Re-use the parsed document structure
                        doc = parsed_doc
            except Exception:
                pass

        # find new types not already in config
        new_types = external_types - set(existing_links.keys())

        if not new_types:
            return

        # Check if we need to create new tables or if they exist
        meadoc_table = doc.get("meadoc")
        if meadoc_table is None:
            meadoc_table = tomlkit.table()
            doc["meadoc"] = meadoc_table

        if "generate" not in meadoc_table:  # type: ignore[operator]
            meadoc_table["generate"] = tomlkit.table()
        generate_table = meadoc_table["generate"]

        if "external-links" not in generate_table:  # type: ignore[operator]
            generate_table["external-links"] = tomlkit.table()
        links_table = generate_table["external-links"]

        # add new types with empty values
        for type_name in sorted(new_types):
            links_table[type_name] = ""  # type: ignore

        # write back to file
        try:
            _ = config_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
        except Exception:
            pass  # silently fail if can't write
