"""error codes and diagnostic classes for meadow.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module defines all error codes, their descriptions, and diagnostic
classes used throughout the meadow codebase for reporting docstring issues.

all errors inherit from `MeadowError` for consistent handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


# constants
ERROR_PREFIX: str = "MDW"


class MeadowError(Exception):
    """base exception for all meadow errors.

    all meadow-specific exceptions inherit from this class, allowing callers
    to catch all meadow errors with a single except clause.

    attributes:
        `message: str`
            human-readable error description
        `location: Location | None`
            where the error occurred (file, line, column)

    examples:
        ```python
        try:
            result = process_file(path)
        except MeadowError as exc:
            print(f"Error at {exc.location}: {exc.message}")
        ```
    """

    message: str
    location: Location | None

    def __init__(
        self,
        message: str,
        location: Location | None = None,
    ) -> None:
        self.message = message
        self.location = location
        super().__init__(message)

    def __str__(self) -> str:
        if self.location:
            return f"{self.location}: {self.message}"
        return self.message


class ConfigError(MeadowError):
    """error in configuration loading or validation."""


class ParseError(MeadowError):
    """error parsing a docstring."""


class ValidationError(MeadowError):
    """error validating a docstring against code."""


class GenerationError(MeadowError):
    """error generating or writing a docstring."""


class ErrorSeverity(Enum):
    """severity levels for diagnostics.

    members:
        `ERROR`
            critical issue that prevents processing
        `WARNING`
            non-critical issue, processing can continue
        `INFO`
            informational message only
    """

    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class ErrorCode(Enum):
    """error codes for meadow diagnostics.

    codes are organised by category:
    - MDW1xx: missing docstring issues
    - MDW2xx: malformed docstring issues
    - MDW3xx: outdated docstring issues

    each code has an associated severity and description.

    attributes:
        `value: str`
            the code string (e.g., "MDW100")

    properties:
        `severity: ErrorSeverity`
            the severity level for this code
        `description: str`
            human-readable description of the error
    """

    # MDW1xx: missing docstring issues
    MISSING_DOCSTRING = "MDW100"
    NOT_AN_MDF_DOCSTRING = "MDW101"
    OTHER_FORMAT_DOCSTRING = "MDW102"

    # MDW2xx: malformed docstring issues
    MALFORMED_MDF_DOCSTRING = "MDW200"
    MISSING_PREAMBLE = "MDW201"
    INVALID_CLASS_DECLARATION = "MDW202"
    INVALID_CLASS_ATTRIBUTE_DECLARATION = "MDW203"
    INVALID_FUNCTION_DECLARATION = "MDW204"
    INVALID_FUNCTION_ARGUMENT_DECLARATION = "MDW205"
    INVALID_VARIABLE_DECLARATION = "MDW206"
    INVALID_RETURN_TYPE_ANNOTATION = "MDW207"
    UNKNOWN_RAISES_CLASS = "MDW208"
    MISSING_BACKTICKS = "MDW209"
    MISSPELLED_SECTION_NAME = "MDW210"
    MISSING_SECTION_COLON = "MDW211"
    INVALID_INDENTATION = "MDW212"
    SECTIONS_OUT_OF_ORDER = "MDW213"
    MULTI_LINE_SUMMARY_FIRST_LINE = "MDW214"
    MULTI_LINE_SUMMARY_SECOND_LINE = "MDW215"
    INCOMPLETE_MDF_DOCSTRING = "MDW216"
    DUPLICATE_CLASS_DECLARATION = "MDW217"
    DUPLICATE_CLASS_ATTRIBUTE_DECLARATION = "MDW218"
    DUPLICATE_FUNCTION_DECLARATION = "MDW219"
    DUPLICATE_FUNCTION_ARGUMENT_DECLARATION = "MDW220"
    DUPLICATE_VARIABLE_DECLARATION = "MDW221"
    DUPLICATE_RETURN_TYPE_ANNOTATION = "MDW222"
    DUPLICATE_RAISES_CLASS = "MDW223"

    # MDW3xx: outdated docstring issues
    OUTDATED_MDF_DOCSTRING = "MDW300"
    OUTDATED_CLASS_DECLARATION = "MDW301"
    OUTDATED_CLASS_ATTRIBUTE_DECLARATION = "MDW302"
    OUTDATED_FUNCTION_DECLARATION = "MDW303"
    OUTDATED_FUNCTION_ARGUMENT_DECLARATION = "MDW304"
    OUTDATED_VARIABLE_DECLARATION = "MDW306"
    OUTDATED_RETURN_TYPE_ANNOTATION = "MDW305"
    OUTDATED_RAISES_CLASS = "MDW307"
    EXTRA_CLASS_DECLARATION = "MDW308"
    EXTRA_CLASS_ATTRIBUTE_DECLARATION = "MDW309"
    EXTRA_FUNCTION_DECLARATION = "MDW310"
    EXTRA_FUNCTION_ARGUMENT_DECLARATION = "MDW311"
    EXTRA_VARIABLE_DECLARATION = "MDW312"
    EXTRA_RETURN_TYPE_ANNOTATION = "MDW313"
    EXTRA_RAISES_CLASS = "MDW314"
    MISSING_CLASS_DECLARATION = "MDW315"
    MISSING_CLASS_ATTRIBUTE_DECLARATION = "MDW316"
    MISSING_FUNCTION_DECLARATION = "MDW317"
    MISSING_FUNCTION_ARGUMENT_DECLARATION = "MDW318"
    MISSING_VARIABLE_DECLARATION = "MDW319"
    MISSING_RETURN_TYPE_ANNOTATION = "MDW320"
    MISSING_RAISES_CLASS = "MDW321"
    MISSING_PREAMBLE_SECTION = "MDW322"
    MISSING_INCOMING_SECTION = "MDW323"
    MISSING_OUTGOING_SECTION = "MDW324"
    MISSING_RETURNS_SECTION = "MDW325"
    MISSING_RAISES_SECTION = "MDW326"

    @property
    def severity(self) -> ErrorSeverity:
        """get the severity level for this error code.

        returns: `ErrorSeverity`
            the severity based on code category
        """
        code_num = int(self.value[3:])

        # MDW1xx: missing docstrings are warnings
        if 100 <= code_num < 200:
            return ErrorSeverity.WARNING

        # MDW2xx: malformed are errors
        if 200 <= code_num < 300:
            return ErrorSeverity.ERROR

        # MDW3xx: outdated are warnings
        if 300 <= code_num < 400:
            return ErrorSeverity.WARNING

        return ErrorSeverity.ERROR

    @property
    def description(self) -> str:
        """get the human-readable description for this error code.

        returns: `str`
            description of what this error means
        """
        descriptions: dict[ErrorCode, str] = {
            ErrorCode.MISSING_DOCSTRING: "missing docstring",
            ErrorCode.NOT_AN_MDF_DOCSTRING: "docstring is not in meadow Docstring Format",
            ErrorCode.OTHER_FORMAT_DOCSTRING: "docstring appears to be in another format (sphinx/google)",
            ErrorCode.MALFORMED_MDF_DOCSTRING: "malformed meadow Docstring Format docstring",
            ErrorCode.MISSING_PREAMBLE: "missing preamble section",
            ErrorCode.INVALID_CLASS_DECLARATION: "invalid class declaration syntax",
            ErrorCode.INVALID_CLASS_ATTRIBUTE_DECLARATION: "invalid class attribute declaration syntax",
            ErrorCode.INVALID_FUNCTION_DECLARATION: "invalid function declaration syntax",
            ErrorCode.INVALID_FUNCTION_ARGUMENT_DECLARATION: "invalid function argument declaration syntax",
            ErrorCode.INVALID_VARIABLE_DECLARATION: "invalid variable declaration syntax",
            ErrorCode.INVALID_RETURN_TYPE_ANNOTATION: "invalid return type annotation",
            ErrorCode.UNKNOWN_RAISES_CLASS: "unknown exception class in raises section",
            ErrorCode.MISSING_BACKTICKS: "missing backticks around code element",
            ErrorCode.MISSPELLED_SECTION_NAME: "misspelled section name",
            ErrorCode.MISSING_SECTION_COLON: "missing colon after section name",
            ErrorCode.INVALID_INDENTATION: "invalid indentation",
            ErrorCode.SECTIONS_OUT_OF_ORDER: "sections are not in the correct order",
            ErrorCode.MULTI_LINE_SUMMARY_FIRST_LINE: "multi-line summary should start on first line",
            ErrorCode.MULTI_LINE_SUMMARY_SECOND_LINE: "multi-line summary should start on second line",
            ErrorCode.INCOMPLETE_MDF_DOCSTRING: "incomplete meadow Docstring Format docstring",
            ErrorCode.DUPLICATE_CLASS_DECLARATION: "duplicate class declaration",
            ErrorCode.DUPLICATE_CLASS_ATTRIBUTE_DECLARATION: "duplicate class attribute declaration",
            ErrorCode.DUPLICATE_FUNCTION_DECLARATION: "duplicate function declaration",
            ErrorCode.DUPLICATE_FUNCTION_ARGUMENT_DECLARATION: "duplicate function argument declaration",
            ErrorCode.DUPLICATE_VARIABLE_DECLARATION: "duplicate variable declaration",
            ErrorCode.DUPLICATE_RETURN_TYPE_ANNOTATION: "duplicate return type annotation",
            ErrorCode.DUPLICATE_RAISES_CLASS: "duplicate raises class",
            ErrorCode.OUTDATED_MDF_DOCSTRING: "outdated meadow Docstring Format docstring",
            ErrorCode.OUTDATED_CLASS_DECLARATION: "outdated class declaration",
            ErrorCode.OUTDATED_CLASS_ATTRIBUTE_DECLARATION: "outdated class attribute declaration",
            ErrorCode.OUTDATED_FUNCTION_DECLARATION: "outdated function declaration",
            ErrorCode.OUTDATED_FUNCTION_ARGUMENT_DECLARATION: "outdated function argument declaration",
            ErrorCode.OUTDATED_VARIABLE_DECLARATION: "outdated variable declaration",
            ErrorCode.OUTDATED_RETURN_TYPE_ANNOTATION: "outdated return type annotation",
            ErrorCode.OUTDATED_RAISES_CLASS: "outdated raises class",
            ErrorCode.EXTRA_CLASS_DECLARATION: "extra class declaration in docstring",
            ErrorCode.EXTRA_CLASS_ATTRIBUTE_DECLARATION: "extra class attribute declaration in docstring",
            ErrorCode.EXTRA_FUNCTION_DECLARATION: "extra function declaration in docstring",
            ErrorCode.EXTRA_FUNCTION_ARGUMENT_DECLARATION: "extra function argument declaration in docstring",
            ErrorCode.EXTRA_VARIABLE_DECLARATION: "extra variable declaration in docstring",
            ErrorCode.EXTRA_RETURN_TYPE_ANNOTATION: "extra return type annotation in docstring",
            ErrorCode.EXTRA_RAISES_CLASS: "extra raises class in docstring",
            ErrorCode.MISSING_CLASS_DECLARATION: "missing class declaration in docstring",
            ErrorCode.MISSING_CLASS_ATTRIBUTE_DECLARATION: "missing class attribute declaration in docstring",
            ErrorCode.MISSING_FUNCTION_DECLARATION: "missing function declaration in docstring",
            ErrorCode.MISSING_FUNCTION_ARGUMENT_DECLARATION: "missing function argument declaration in docstring",
            ErrorCode.MISSING_VARIABLE_DECLARATION: "missing variable declaration in docstring",
            ErrorCode.MISSING_RETURN_TYPE_ANNOTATION: "missing return type annotation in docstring",
            ErrorCode.MISSING_RAISES_CLASS: "missing raises class in docstring",
            ErrorCode.MISSING_PREAMBLE_SECTION: "missing preamble section",
            ErrorCode.MISSING_INCOMING_SECTION: "missing incoming signatures section",
            ErrorCode.MISSING_OUTGOING_SECTION: "missing outgoing signatures section",
            ErrorCode.MISSING_RETURNS_SECTION: "missing returns section",
            ErrorCode.MISSING_RAISES_SECTION: "missing raises section",
        }
        return descriptions.get(self, "unknown error")


@dataclass(frozen=True, slots=True)
class Location:
    """location in a source file.

    used to pinpoint exactly where an error or diagnostic occurred.

    attributes:
        `line: int`
            line number (1-indexed)
        `column: int`
            column number (0-indexed)
        `file: str | None`
            path to the source file, or None if not applicable

    examples:
        ```python
        loc = Location(line=42, column=5, file="src/main.py")
        print(loc)  # "src/main.py:42:5"
        ```
    """

    line: int
    column: int
    file: str | None = None

    def __str__(self) -> str:
        """format location as "file:line:column" or "line X, column Y"."""
        if self.file:
            return f"{self.file}:{self.line}:{self.column}"
        return f"line {self.line}, column {self.column}"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """a single diagnostic message.

    represents one issue found during parsing or validation, with
    location information and severity level.

    attributes:
        `code: ErrorCode`
            the error code for this diagnostic
        `message: str`
            human-readable description
        `line: int`
            line number where the issue occurred
        `column: int`
            column number where the issue occurred
        `severity: ErrorSeverity`
            severity level (auto-derived from code if not specified)

    examples:
        ```python
        diag = Diagnostic(
            code=ErrorCode.MISSING_PREAMBLE,
            message="docstring missing preamble",
            line=10,
            column=0,
        )
        print(diag)  # "MDW201: docstring missing preamble (line 10, col 0)"
        ```
    """

    code: ErrorCode
    message: str
    line: int
    column: int
    severity: ErrorSeverity = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", self.code.severity)

    def __str__(self) -> str:
        """format diagnostic as "CODE: message (location)"."""
        return f"{self.code.value}: {self.message} (line {self.line}, col {self.column})"


class DiagnosticCollection:
    """collection of diagnostics for a file or project.

    aggregates multiple diagnostics and provides filtering by severity
    and iteration support.

    attributes:
        `diagnostics: list[Diagnostic]`
            the list of collected diagnostics

    examples:
        ```python
        coll = DiagnosticCollection()
        coll.add_error(ErrorCode.MISSING_DOCSTRING, "no docstring", line=1)

        if coll.has_errors():
            for diag in coll.get_by_severity(ErrorSeverity.ERROR):
                print(diag)
        ```
    """

    def __init__(self) -> None:
        """initialise an empty diagnostic collection."""
        self.diagnostics: list[Diagnostic] = []

    def add(self, diagnostic: Diagnostic) -> None:
        """add a diagnostic to the collection.

        arguments:
            `diagnostic: Diagnostic`
                the diagnostic to add
        """
        self.diagnostics.append(diagnostic)

    def add_error(
        self,
        code: ErrorCode,
        message: str,
        line: int,
        column: int = 0,
    ) -> None:
        """convenience method to add an error diagnostic.

        arguments:
            `code: ErrorCode`
                the error code
            `message: str`
                human-readable description
            `line: int`
                line number
            `column: int = 0`
                column number (defaults to 0)
        """
        self.add(Diagnostic(code, message, line, column))

    def has_errors(self) -> bool:
        """check if there are any error-level diagnostics.

        returns: `bool`
            True if any diagnostic has ERROR severity
        """
        return any(d.severity == ErrorSeverity.ERROR for d in self.diagnostics)

    def has_warnings(self) -> bool:
        """check if there are any warning-level diagnostics.

        returns: `bool`
            True if any diagnostic has WARNING severity
        """
        return any(
            d.severity == ErrorSeverity.WARNING for d in self.diagnostics
        )

    def get_by_severity(self, severity: ErrorSeverity) -> list[Diagnostic]:
        """get all diagnostics of a specific severity.

        arguments:
            `severity: ErrorSeverity`
                the severity level to filter by

        returns: `list[Diagnostic]`
            all diagnostics with the specified severity
        """
        return [d for d in self.diagnostics if d.severity == severity]

    def __len__(self) -> int:
        """return the number of diagnostics in the collection."""
        return len(self.diagnostics)

    def __iter__(self) -> Iterator[Diagnostic]:
        """iterate over all diagnostics in the collection."""
        return iter(self.diagnostics)
