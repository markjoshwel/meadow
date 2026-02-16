"""test the # meadow: ignore comment feature.

with all my heart, 2025-2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

from meadoc.validator import MDFValidator, analyse_file


class TestMeadowIgnore:
    """test the # meadow: ignore comment feature."""

    def test_ignore_single_line_docstring(self) -> None:
        """test that # meadow: ignore works with single-line docstrings."""
        code = '''
def example() -> None:
    """a function with non-mdf docstring."""  # meadow: ignore
    pass
'''
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            elements = analyse_file(path)
            assert elements is not None
            # find the function element
            func_element = next(
                (e for e in elements if e.name == "example"), None
            )
            assert func_element is not None
            assert func_element.ignore is True

            # validate should produce no errors for ignored element
            validator = MDFValidator()
            diagnostics = validator.validate_file(path)
            assert not diagnostics.has_errors()
        finally:
            path.unlink()

    def test_ignore_multi_line_docstring(self) -> None:
        """test that # meadow: ignore works with multi-line docstrings."""
        code = '''
def example() -> None:
    """
    a function with non-mdf docstring.

    this is not in proper MDF format.
    """  # meadow: ignore
    pass
'''
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            elements = analyse_file(path)
            assert elements is not None
            func_element = next(
                (e for e in elements if e.name == "example"), None
            )
            assert func_element is not None
            assert func_element.ignore is True

            validator = MDFValidator()
            diagnostics = validator.validate_file(path)
            assert not diagnostics.has_errors()
        finally:
            path.unlink()

    def test_no_ignore_produces_warning(self) -> None:
        """test that non-MDF docstrings without ignore comment produce warnings."""
        code = '''
def example() -> None:
    """a function with non-mdf docstring."""
    pass
'''
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            elements = analyse_file(path)
            assert elements is not None
            func_element = next(
                (e for e in elements if e.name == "example"), None
            )
            assert func_element is not None
            assert func_element.ignore is False

            validator = MDFValidator()
            diagnostics = validator.validate_file(path)
            # should have MDW101 warning for non-MDF docstring
            # (MDW101 is a WARNING, not an ERROR)
            assert len(diagnostics) > 0
        finally:
            path.unlink()

    def test_ignore_on_next_line(self) -> None:
        """test that # meadow: ignore works when on the line after docstring."""
        code = '''
def example() -> None:
    """
    a function with non-mdf docstring.
    """
    # meadow: ignore
    pass
'''
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)

        try:
            elements = analyse_file(path)
            assert elements is not None
            func_element = next(
                (e for e in elements if e.name == "example"), None
            )
            assert func_element is not None
            assert func_element.ignore is True
        finally:
            path.unlink()
