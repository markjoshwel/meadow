"""tests for meadow errors module

with all my heart, 2024-2025, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""

from meadoc.errors import (
    Diagnostic,
    DiagnosticCollection,
    ErrorCode,
    ErrorSeverity,
)


class TestErrorCodes:
    """test suite for error codes"""

    def test_all_error_codes_have_severity(self) -> None:
        """Test that all error codes have a severity property"""
        for code in ErrorCode:
            severity = code.severity
            assert isinstance(severity, ErrorSeverity)

    def test_all_error_codes_have_description(self) -> None:
        """Test that all error codes have a description property"""
        for code in ErrorCode:
            desc = code.description
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_missing_docstring_is_warning(self) -> None:
        """Test that missing docstring is a warning"""
        severity = ErrorCode.MISSING_DOCSTRING.severity
        assert severity == ErrorSeverity.WARNING

    def test_malformed_docstring_is_error(self) -> None:
        """Test that malformed docstring is an error"""
        severity = ErrorCode.MALFORMED_MDF_DOCSTRING.severity
        assert severity == ErrorSeverity.ERROR


class TestDiagnostic:
    """test suite for Diagnostic class"""

    def test_diagnostic_creation(self) -> None:
        """Test creating a diagnostic"""
        diag = Diagnostic(
            code=ErrorCode.MISSING_DOCSTRING,
            message="test message",
            line=10,
            column=5,
        )

        assert diag.code == ErrorCode.MISSING_DOCSTRING
        assert diag.message == "test message"
        assert diag.line == 10
        assert diag.column == 5
        assert diag.severity == ErrorSeverity.WARNING

    def test_diagnostic_string_representation(self) -> None:
        """Test diagnostic string representation"""
        diag = Diagnostic(
            code=ErrorCode.MISSING_PREAMBLE,
            message="missing preamble",
            line=1,
            column=0,
        )

        str_repr = str(diag)
        assert "MDW201" in str_repr
        assert "missing preamble" in str_repr
        assert "line 1" in str_repr


class TestDiagnosticCollection:
    """test suite for DiagnosticCollection"""

    def test_empty_collection(self) -> None:
        """Test empty diagnostic collection"""
        coll = DiagnosticCollection()
        assert len(coll) == 0
        assert not coll.has_errors()
        assert not coll.has_warnings()

    def test_add_diagnostic(self) -> None:
        """Test adding diagnostics"""
        coll = DiagnosticCollection()
        diag = Diagnostic(
            code=ErrorCode.MISSING_DOCSTRING,
            message="test",
            line=1,
            column=0,
        )

        coll.add(diag)
        assert len(coll) == 1

    def test_add_error_convenience(self) -> None:
        """Test add_error convenience method"""
        coll = DiagnosticCollection()
        coll.add_error(
            ErrorCode.MALFORMED_MDF_DOCSTRING,
            "test error",
            line=5,
            column=10,
        )

        assert len(coll) == 1
        assert coll.has_errors()

    def test_filter_by_severity(self) -> None:
        """Test filtering diagnostics by severity"""
        coll = DiagnosticCollection()

        # add warning
        coll.add(
            Diagnostic(
                code=ErrorCode.MISSING_DOCSTRING,
                message="warning",
                line=1,
                column=0,
            )
        )

        # add error
        coll.add(
            Diagnostic(
                code=ErrorCode.MALFORMED_MDF_DOCSTRING,
                message="error",
                line=2,
                column=0,
            )
        )

        errors = coll.get_by_severity(ErrorSeverity.ERROR)
        warnings = coll.get_by_severity(ErrorSeverity.WARNING)

        assert len(errors) == 1
        assert len(warnings) == 1
        assert errors[0].code == ErrorCode.MALFORMED_MDF_DOCSTRING
        assert warnings[0].code == ErrorCode.MISSING_DOCSTRING

    def test_iteration(self) -> None:
        """Test iterating over diagnostics"""
        coll = DiagnosticCollection()
        coll.add_error(ErrorCode.MISSING_DOCSTRING, "test1", 1)
        coll.add_error(ErrorCode.MISSING_PREAMBLE, "test2", 2)

        codes = [d.code for d in coll]
        assert len(codes) == 2
        assert ErrorCode.MISSING_DOCSTRING in codes
        assert ErrorCode.MISSING_PREAMBLE in codes
