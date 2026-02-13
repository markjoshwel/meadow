"""meadow Docstring Format (MDF) parser.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module provides parsing capabilities for the meadow Docstring Format,
converting docstrings into a structured representation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TypeVar

from meadow.errors import DiagnosticCollection, ErrorCode, Location

T = TypeVar("T", "ParameterDoc", "FunctionDoc", "ExceptionDoc", "ReturnDoc")


class SectionType(Enum):
    """types of sections in an MDF docstring.

    members:
        `PREAMBLE` - initial description line
        `BODY` - additional description text
        `ATTRIBUTES` - class attributes
        `ARGUMENTS` - function arguments
        `PARAMETERS` - alternative name for arguments
        `FUNCTIONS` - module-level functions
        `METHODS` - class methods
        `RETURNS` - return type annotation
        `RAISES` - exception classes
        `USAGE` - usage examples
        `UNKNOWN` - unrecognised section
    """

    PREAMBLE = auto()
    BODY = auto()
    ATTRIBUTES = auto()
    ARGUMENTS = auto()
    PARAMETERS = auto()
    FUNCTIONS = auto()
    METHODS = auto()
    RETURNS = auto()
    RAISES = auto()
    USAGE = auto()
    UNKNOWN = auto()


# section headers that trigger MDF parsing
SECTION_HEADERS: dict[str, SectionType] = {
    "attributes:": SectionType.ATTRIBUTES,
    "arguments:": SectionType.ARGUMENTS,
    "parameters:": SectionType.PARAMETERS,
    "functions:": SectionType.FUNCTIONS,
    "methods:": SectionType.METHODS,
    "returns:": SectionType.RETURNS,
    "raises:": SectionType.RAISES,
    "usage:": SectionType.USAGE,
    "examples:": SectionType.USAGE,
}

# section order for validation (lower = earlier in docstring)
SECTION_ORDER: dict[SectionType, int] = {
    SectionType.PREAMBLE: 0,
    SectionType.BODY: 1,
    SectionType.ATTRIBUTES: 2,
    SectionType.ARGUMENTS: 2,
    SectionType.PARAMETERS: 2,
    SectionType.FUNCTIONS: 3,
    SectionType.METHODS: 3,
    SectionType.RETURNS: 4,
    SectionType.RAISES: 5,
    SectionType.USAGE: 6,
    SectionType.UNKNOWN: 99,
}


@dataclass
class ParameterDoc:
    """documentation for a single parameter or attribute.

    attributes:
        `name: str`
            parameter name
        `type_annotation: str`
            type annotation (may be empty)
        `default_value: str | None`
            default value if any
        `description: list[str]`
            description lines
        `location: Location | None`
            source location
    """

    name: str
    type_annotation: str
    default_value: str | None
    description: list[str] = field(default_factory=list)
    location: Location | None = None


@dataclass
class FunctionDoc:
    """documentation for a function or method signature.

    attributes:
        `signature: str`
            function signature text
        `description: list[str]`
            description lines
        `location: Location | None`
            source location
    """

    signature: str
    description: list[str] = field(default_factory=list)
    location: Location | None = None


@dataclass
class ExceptionDoc:
    """documentation for an exception in raises section.

    attributes:
        `exception_class: str`
            exception class name
        `description: list[str]`
            description lines
        `location: Location | None`
            source location
    """

    exception_class: str
    description: list[str] = field(default_factory=list)
    location: Location | None = None


@dataclass
class ReturnDoc:
    """documentation for return type.

    attributes:
        `type_annotation: str`
            return type annotation
        `description: list[str]`
            description lines
        `location: Location | None`
            source location
    """

    type_annotation: str
    description: list[str] = field(default_factory=list)
    location: Location | None = None


@dataclass
class Section:
    """a section within an MDF docstring.

    attributes:
        `section_type: SectionType`
            type of section
        `content: list[str]`
            raw content lines
        `items: list[ParameterDoc | FunctionDoc | ExceptionDoc | ReturnDoc]`
            parsed items within section
        `location: Location | None`
            source location
    """

    section_type: SectionType
    content: list[str] = field(default_factory=list)
    items: list[ParameterDoc | FunctionDoc | ExceptionDoc | ReturnDoc] = field(
        default_factory=list
    )
    location: Location | None = None


@dataclass
class ParsedDocstring:
    """fully parsed MDF docstring.

    attributes:
        `preamble: str`
            first line description
        `body: list[str]`
            body text lines
        `sections: list[Section]`
            parsed sections
        `raw_text: str`
            original docstring text
        `is_mdf: bool`
            whether docstring follows MDF format
        `diagnostics: DiagnosticCollection`
            parsing diagnostics
    """

    preamble: str = ""
    body: list[str] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    raw_text: str = ""
    is_mdf: bool = False
    diagnostics: DiagnosticCollection = field(
        default_factory=DiagnosticCollection
    )

    def get_section(self, section_type: SectionType) -> Section | None:
        """Get a section by type.

        arguments:
            `section_type: SectionType`
                the section type to find

        returns: `Section | None`
            the section if found, None otherwise
        """
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None

    def has_section(self, section_type: SectionType) -> bool:
        """Check if docstring has a specific section.

        arguments:
            `section_type: SectionType`
                the section type to check

        returns: `bool`
            True if section exists
        """
        return any(s.section_type == section_type for s in self.sections)


class MDFParser:
    """parser for meadow Docstring Format.

    Parses docstrings into structured representations with diagnostic
    information about any formatting issues.

    examples:
        ```python
        parser = MDFParser("src/main.py")
        result = parser.parse(docstring, line_offset=10)

        if result.is_mdf:
            print(result.preamble)
            for section in result.sections:
                print(section.section_type)
        ```
    """

    file_path: str | None
    diagnostics: DiagnosticCollection

    def __init__(self, file_path: str | None = None) -> None:
        """Initialise the parser.

        arguments:
            `file_path: str | None = None`
                path to source file for location tracking

        returns: `none`
            no return value
        """
        self.file_path = file_path
        self.diagnostics = DiagnosticCollection()

    def parse(self, docstring: str, line_offset: int = 1) -> ParsedDocstring:
        """Parse a docstring into a structured representation.

        arguments:
            `docstring: str`
                the docstring to parse
            `line_offset: int = 1`
                starting line number in source file

        returns: `ParsedDocstring`
            parsed docstring with diagnostics
        """
        result = ParsedDocstring(raw_text=docstring)
        self.diagnostics = DiagnosticCollection()

        if not docstring.strip():
            return result

        lines = docstring.split("\n")

        # check for other docstring formats
        if self._looks_like_other_format(docstring):
            self.diagnostics.add_error(
                ErrorCode.OTHER_FORMAT_DOCSTRING,
                "docstring appears to be in another format (sphinx/google style)",
                line_offset,
            )
            result.diagnostics = self.diagnostics
            return result

        # parse the docstring
        current_section: Section | None = None
        in_code_block = False

        for i, line in enumerate(lines):
            line_num = line_offset + i
            stripped = line.strip()

            # handle code blocks
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                if current_section:
                    current_section.content.append(line)
                else:
                    result.body.append(line)
                continue

            if in_code_block:
                if current_section:
                    current_section.content.append(line)
                else:
                    result.body.append(line)
                continue

            # check for section headers
            section_type = self._detect_section_header(stripped)

            if section_type != SectionType.UNKNOWN:
                result.is_mdf = True
                current_section = Section(
                    section_type=section_type,
                    location=Location(line_num, 0, self.file_path),
                )
                result.sections.append(current_section)
                current_section.content.append(line)
                continue

            # handle content
            if current_section is None:
                # preamble or body
                if i == 0 or (i == 1 and not lines[0].strip()):
                    if stripped:
                        result.preamble = stripped
                else:
                    result.body.append(line)
            else:
                current_section.content.append(line)

        # parse section contents
        for section in result.sections:
            self._parse_section_content(section)

        # validate preamble
        if result.is_mdf and not result.preamble:
            self.diagnostics.add_error(
                ErrorCode.MISSING_PREAMBLE,
                "MDF docstring missing preamble",
                line_offset,
            )

        # validate section order
        self._validate_section_order(result, line_offset)

        result.diagnostics = self.diagnostics
        return result

    def _detect_section_header(self, line: str) -> SectionType:
        """Detect if a line is a section header.

        arguments:
            `line: str`
                line to check

        returns: `SectionType`
            detected section type or UNKNOWN
        """
        lower = line.lower().rstrip()

        # direct match
        if lower in SECTION_HEADERS:
            return SECTION_HEADERS[lower]

        # check with colon
        if lower + ":" in SECTION_HEADERS:
            return SECTION_HEADERS[lower + ":"]

        # check if line starts with a section header
        for header, section_type in SECTION_HEADERS.items():
            if lower.startswith(header):
                return section_type

        return SectionType.UNKNOWN

    def _looks_like_other_format(self, docstring: str) -> bool:
        """Check if docstring looks like sphinx or google format.

        arguments:
            `docstring: str`
                docstring to check

        returns: `bool`
            True if appears to be another format
        """
        # sphinx patterns
        sphinx_patterns = [
            r":param\s+\w+:",
            r":returns?:",
            r":raises?:",
            r":type\s+\w+:",
            r":rtype:",
        ]

        # google patterns
        google_patterns = [
            r"^\s*Args:\s*$",
            r"^\s*Returns:\s*$",
            r"^\s*Raises:\s*$",
            r"^\s*Yields:\s*$",
            r"^\s*Examples:\s*$",
        ]

        for pattern in sphinx_patterns:
            if re.search(pattern, docstring, re.MULTILINE):
                return True

        for pattern in google_patterns:
            if re.search(pattern, docstring, re.MULTILINE):
                return True

        return False

    def _parse_section_content(self, section: Section) -> None:
        """Parse the content of a section.

        arguments:
            `section: Section`
                section to parse

        returns: `none`
            no return value
        """
        if section.section_type in (
            SectionType.ATTRIBUTES,
            SectionType.ARGUMENTS,
            SectionType.PARAMETERS,
        ):
            section.items.extend(
                self._parse_parameters(section.content, section.location)
            )
        elif section.section_type in (
            SectionType.FUNCTIONS,
            SectionType.METHODS,
        ):
            section.items.extend(
                self._parse_functions(section.content, section.location)
            )
        elif section.section_type == SectionType.RAISES:
            section.items.extend(
                self._parse_raises(section.content, section.location)
            )
        elif section.section_type == SectionType.RETURNS:
            section.items.extend(
                self._parse_returns(section.content, section.location)
            )

    def _parse_parameters(
        self, content: list[str], base_location: Location | None
    ) -> list[ParameterDoc]:
        """Parse parameter or attribute declarations.

        arguments:
            `content: list[str]`
                section content lines
            `base_location: Location | None`
                base location for line numbers

        returns: `list[ParameterDoc]`
            parsed parameters
        """
        parameters: list[ParameterDoc] = []
        current_param: ParameterDoc | None = None

        for i, line in enumerate(content):
            stripped = line.strip()

            if not stripped:
                continue

            # check for backtick-wrapped declaration
            if stripped.startswith("`") and "`" in stripped[1:]:
                if current_param:
                    parameters.append(current_param)

                backtick_end = stripped.find("`", 1)
                if backtick_end > 0:
                    declaration = stripped[1:backtick_end]
                    desc = stripped[backtick_end + 1 :].strip()

                    name, type_ann, default = self._parse_declaration(
                        declaration
                    )

                    line_num = (base_location.line if base_location else 0) + i
                    current_param = ParameterDoc(
                        name=name,
                        type_annotation=type_ann,
                        default_value=default,
                        description=[desc] if desc else [],
                        location=Location(
                            line_num,
                            line.index("`"),
                            base_location.file if base_location else None,
                        ),
                    )
            elif current_param is not None:
                current_param.description.append(stripped)

        if current_param:
            parameters.append(current_param)

        return parameters

    def _parse_functions(
        self, content: list[str], base_location: Location | None
    ) -> list[FunctionDoc]:
        """Parse function or method declarations.

        arguments:
            `content: list[str]`
                section content lines
            `base_location: Location | None`
                base location for line numbers

        returns: `list[FunctionDoc]`
            parsed functions
        """
        functions: list[FunctionDoc] = []
        current_func: FunctionDoc | None = None
        collecting_signature = False
        signature_lines: list[str] = []

        for i, line in enumerate(content):
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("`def ") or stripped.startswith(
                "`async def "
            ):
                if current_func:
                    functions.append(current_func)

                collecting_signature = True
                signature_lines = [stripped]

                if stripped.endswith("`"):
                    collecting_signature = False
                    signature = stripped[1:-1]
                    line_num = (base_location.line if base_location else 0) + i
                    current_func = FunctionDoc(
                        signature=signature,
                        location=Location(
                            line_num,
                            line.index("`"),
                            base_location.file if base_location else None,
                        ),
                    )
            elif collecting_signature:
                signature_lines.append(stripped)
                if stripped.endswith("`"):
                    collecting_signature = False
                    full_sig = " ".join(
                        s.strip().rstrip("`") for s in signature_lines
                    )
                    full_sig = full_sig.lstrip("`")
                    line_num = (base_location.line if base_location else 0) + i
                    current_func = FunctionDoc(
                        signature=full_sig,
                        location=Location(
                            line_num,
                            0,
                            base_location.file if base_location else None,
                        ),
                    )
            elif current_func is not None:
                current_func.description.append(stripped)

        if current_func:
            functions.append(current_func)

        return functions

    def _parse_raises(
        self, content: list[str], base_location: Location | None
    ) -> list[ExceptionDoc]:
        """Parse raises section content.

        arguments:
            `content: list[str]`
                section content lines
            `base_location: Location | None`
                base location for line numbers

        returns: `list[ExceptionDoc]`
            parsed exceptions
        """
        exceptions: list[ExceptionDoc] = []
        current_exc: ExceptionDoc | None = None

        for i, line in enumerate(content):
            stripped = line.strip()

            if not stripped:
                continue

            # single-line format: raises: `Exception`
            if stripped.lower().startswith("raises:") and "`" in stripped:
                backtick_start = stripped.find("`")
                backtick_end = stripped.find("`", backtick_start + 1)
                if backtick_end > backtick_start:
                    exc_class = stripped[backtick_start + 1 : backtick_end]
                    desc = stripped[backtick_end + 1 :].strip()
                    line_num = (base_location.line if base_location else 0) + i
                    exceptions.append(
                        ExceptionDoc(
                            exception_class=exc_class,
                            description=[desc] if desc else [],
                            location=Location(
                                line_num,
                                backtick_start,
                                base_location.file if base_location else None,
                            ),
                        )
                    )
                continue

            # multi-line format
            if stripped.startswith("`") and "`" in stripped[1:]:
                if current_exc:
                    exceptions.append(current_exc)

                backtick_end = stripped.find("`", 1)
                exc_class = stripped[1:backtick_end]
                desc = stripped[backtick_end + 1 :].strip()
                line_num = (base_location.line if base_location else 0) + i
                current_exc = ExceptionDoc(
                    exception_class=exc_class,
                    description=[desc] if desc else [],
                    location=Location(
                        line_num,
                        line.index("`"),
                        base_location.file if base_location else None,
                    ),
                )
            elif current_exc is not None:
                current_exc.description.append(stripped)

        if current_exc:
            exceptions.append(current_exc)

        return exceptions

    def _parse_returns(
        self, content: list[str], base_location: Location | None
    ) -> list[ReturnDoc]:
        """Parse returns section content.

        arguments:
            `content: list[str]`
                section content lines
            `base_location: Location | None`
                base location for line numbers

        returns: `list[ReturnDoc]`
            parsed return types
        """
        returns: list[ReturnDoc] = []
        current_return: ReturnDoc | None = None

        for i, line in enumerate(content):
            stripped = line.strip()

            if not stripped:
                continue

            # single-line format: returns: `Type`
            if stripped.lower().startswith("returns:") and "`" in stripped:
                if current_return:
                    returns.append(current_return)

                backtick_start = stripped.find("`")
                backtick_end = stripped.find("`", backtick_start + 1)
                if backtick_end > backtick_start:
                    type_ann = stripped[backtick_start + 1 : backtick_end]
                    desc = stripped[backtick_end + 1 :].strip()
                    line_num = (base_location.line if base_location else 0) + i
                    current_return = ReturnDoc(
                        type_annotation=type_ann,
                        description=[desc] if desc else [],
                        location=Location(
                            line_num,
                            backtick_start,
                            base_location.file if base_location else None,
                        ),
                    )
                continue

            # multi-line format
            if stripped.startswith("`") and "`" in stripped[1:]:
                if current_return:
                    returns.append(current_return)

                backtick_end = stripped.find("`", 1)
                type_ann = stripped[1:backtick_end]
                desc = stripped[backtick_end + 1 :].strip()
                line_num = (base_location.line if base_location else 0) + i
                current_return = ReturnDoc(
                    type_annotation=type_ann,
                    description=[desc] if desc else [],
                    location=Location(
                        line_num,
                        line.index("`"),
                        base_location.file if base_location else None,
                    ),
                )
            elif current_return is not None:
                current_return.description.append(stripped)

        if current_return:
            returns.append(current_return)

        return returns

    def _parse_declaration(
        self, declaration: str
    ) -> tuple[str, str, str | None]:
        """Parse a variable declaration like 'name: str = "default"'.

        arguments:
            `declaration: str`
                declaration string without backticks

        returns: `tuple[str, str, str | None]`
            (name, type_annotation, default_value)
        """
        name = ""
        type_ann = ""
        default = None

        if ":" in declaration:
            colon_pos = declaration.index(":")
            name = declaration[:colon_pos].strip()
            rest = declaration[colon_pos + 1 :].strip()

            if "=" in rest:
                eq_pos = rest.index("=")
                type_ann = rest[:eq_pos].strip()
                default = rest[eq_pos + 1 :].strip()
            else:
                type_ann = rest
        else:
            name = declaration.strip()

        return name, type_ann, default

    def _validate_section_order(
        self, parsed: ParsedDocstring, line_offset: int
    ) -> None:
        """Validate that sections are in correct order.

        arguments:
            `parsed: ParsedDocstring`
                parsed docstring to validate
            `line_offset: int`
                starting line number

        returns: `none`
            no return value
        """
        last_order = -1
        for section in parsed.sections:
            current_order = SECTION_ORDER.get(section.section_type, 99)
            if current_order < last_order:
                line_num = (
                    section.location.line if section.location else line_offset
                )
                self.diagnostics.add_error(
                    ErrorCode.SECTIONS_OUT_OF_ORDER,
                    f"section '{section.section_type.name}' is out of order",
                    line_num,
                )
            last_order = current_order


def parse_docstring(
    docstring: str, file_path: str | None = None, line_offset: int = 1
) -> ParsedDocstring:
    """Convenience function to parse a docstring.

    arguments:
        `docstring: str`
            the docstring to parse
        `file_path: str | None = None`
            path to source file
        `line_offset: int = 1`
            starting line number

    returns: `ParsedDocstring`
        parsed docstring structure
    """
    parser = MDFParser(file_path)
    return parser.parse(docstring, line_offset)
