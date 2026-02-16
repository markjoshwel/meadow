"""tests for meadow parser
with all my heart, 2024-2025, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""


from meadoc.errors import ErrorCode
from meadoc.parser import (
    ParameterDoc,
    SectionType,
    parse_docstring,
)


class TestMDFParser:
    """test suite for MDF parser"""

    def test_parse_empty_docstring(self) -> None:
        """Test parsing empty docstring"""
        result = parse_docstring("")
        assert result.preamble == ""
        assert result.body == []
        assert result.sections == []
        assert not result.is_mdf

    def test_parse_simple_preamble(self) -> None:
        """Test parsing simple preamble"""
        result = parse_docstring("a simple function")
        assert result.preamble == "a simple function"
        assert not result.is_mdf

    def test_parse_preamble_with_body(self) -> None:
        """Test parsing preamble with body text"""
        docstring = """a simple function

this is a longer description
that spans multiple lines
"""
        result = parse_docstring(docstring)
        assert result.preamble == "a simple function"
        assert len(result.body) > 0

    def test_parse_with_attributes(self) -> None:
        """Test parsing class with attributes"""
        docstring = """a simple class

attributes:
    `name: str`
        the name attribute
    `count: int = 0`
        the count attribute
"""
        result = parse_docstring(docstring)
        assert result.is_mdf
        assert result.has_section(SectionType.ATTRIBUTES)

        attrs_section = result.get_section(SectionType.ATTRIBUTES)
        assert attrs_section is not None
        assert len(attrs_section.items) == 2

        # check first attribute
        attr1 = attrs_section.items[0]
        assert isinstance(attr1, ParameterDoc)
        assert attr1.name == "name"
        assert attr1.type_annotation == "str"

        # check second attribute with default
        attr2 = attrs_section.items[1]
        assert isinstance(attr2, ParameterDoc)
        assert attr2.name == "count"
        assert attr2.type_annotation == "int"
        assert attr2.default_value == "0"

    def test_parse_with_arguments(self) -> None:
        """Test parsing function with arguments"""
        docstring = """a simple function

arguments:
    `x: int`
        the x parameter
    `y: str | None = None`
        the y parameter
"""
        result = parse_docstring(docstring)
        assert result.is_mdf

        args_section = result.get_section(SectionType.ARGUMENTS)
        assert args_section is not None
        assert len(args_section.items) == 2

    def test_parse_with_returns(self) -> None:
        """Test parsing function with return type"""
        docstring = """a simple function

returns: `bool`
    true if successful
"""
        result = parse_docstring(docstring)
        assert result.is_mdf

        returns_section = result.get_section(SectionType.RETURNS)
        assert returns_section is not None
        assert len(returns_section.items) == 1

    def test_parse_with_raises(self) -> None:
        """Test parsing function with raises"""
        docstring = """a simple function

raises:
    `ValueError`
        when input is invalid
    `TypeError`
        when type is wrong
"""
        result = parse_docstring(docstring)
        assert result.is_mdf

        raises_section = result.get_section(SectionType.RAISES)
        assert raises_section is not None
        assert len(raises_section.items) == 2

    def test_parse_with_methods(self) -> None:
        """Test parsing class with methods"""
        docstring = """a simple class

methods:
    `def method1(self) -> int`
        first method
    `def method2(self, x: str) -> None`
        second method
"""
        result = parse_docstring(docstring)
        assert result.is_mdf

        methods_section = result.get_section(SectionType.METHODS)
        assert methods_section is not None
        assert len(methods_section.items) == 2

    def test_detects_other_format_sphinx(self) -> None:
        """Test detection of sphinx-style docstrings"""
        docstring = """a simple function

:param x: the x parameter
:returns: the result
"""
        result = parse_docstring(docstring)
        assert not result.is_mdf
        assert any(
            d.code == ErrorCode.OTHER_FORMAT_DOCSTRING
            for d in result.diagnostics
        )

    def test_detects_other_format_google(self) -> None:
        """Test detection of google-style docstrings"""
        docstring = """a simple function

Args:
    x: the x parameter

Returns:
    the result
"""
        result = parse_docstring(docstring)
        assert not result.is_mdf
        assert any(
            d.code == ErrorCode.OTHER_FORMAT_DOCSTRING
            for d in result.diagnostics
        )

    def test_missing_preamble_error(self) -> None:
        """Test error when preamble is missing"""
        docstring = """

arguments:
    `x: int`
        the x parameter
"""
        result = parse_docstring(docstring)
        assert result.is_mdf
        assert any(
            d.code == ErrorCode.MISSING_PREAMBLE for d in result.diagnostics
        )


class TestParseDocstringFunction:
    """test the parse_docstring convenience function"""

    def test_basic_usage(self) -> None:
        """Test basic usage of parse_docstring"""
        result = parse_docstring(
            "test preamble", file_path="test.py", line_offset=10
        )
        assert result.preamble == "test preamble"

    def test_with_complex_docstring(self) -> None:
        """Test parsing complex docstring"""
        docstring = '''"""a complex function

does many things in a complex way

arguments:
    `data: dict[str, Any]`
        input data to process
    `options: Options | None = None`
        optional processing options

returns: `Result[T]`
    the processed result

raises:
    `ValueError`
        when data is invalid
    `ProcessingError`
        when processing fails

usage:
    ```python
    result = process_data({"key": "value"})
    ```
"""'''

        result = parse_docstring(docstring)
        assert result.is_mdf
        assert result.preamble == '"""a complex function'
        assert result.has_section(SectionType.ARGUMENTS)
        assert result.has_section(SectionType.RETURNS)
        assert result.has_section(SectionType.RAISES)
