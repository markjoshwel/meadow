"""validator for meadow Docstring Format.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module provides validation of MDF docstrings against actual Python code,
detecting issues like outdated information, missing sections, and malformed syntax.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from meadow.config import Config
from meadow.errors import Diagnostic, DiagnosticCollection, ErrorCode
from meadow.parser import MDFParser, ParameterDoc, ParsedDocstring, SectionType


@dataclass
class CodeElement:
    """represents a code element (function, class, method, etc.).

    attributes:
        `name: str`
            element name (e.g., "MyClass.method")
        `element_type: str`
            one of: 'module', 'class', 'function', 'method'
        `docstring: str | None`
            docstring text if present
        `line_number: int`
            line number in source file
        `arguments: list[tuple[str, str | None, str | None]]`
            argument info: (name, type_annotation, default_value)
        `return_annotation: str | None`
            return type annotation
        `attributes: list[tuple[str, str | None]]`
            attribute info: (name, type_annotation)
        `raises: list[str]`
            exception classes mentioned
    """

    name: str
    element_type: str
    docstring: str | None = None
    line_number: int = 0
    arguments: list[tuple[str, str | None, str | None]] = field(
        default_factory=list
    )
    return_annotation: str | None = None
    attributes: list[tuple[str, str | None]] = field(default_factory=list)
    raises: list[str] = field(default_factory=list)


def analyse_file(file_path: Path) -> list[CodeElement] | None:
    """Analyse a Python file and extract all code elements.

    Pure function that reads and parses a file, returning structured
    information about all documented elements.

    arguments:
        `file_path: Path`
            path to the Python file

    returns: `list[CodeElement] | None`
        list of code elements, or None if file cannot be parsed
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return None

    elements: list[CodeElement] = []

    # add module-level element
    module_doc = ast.get_docstring(tree)
    elements.append(
        CodeElement(
            name=file_path.stem,
            element_type="module",
            docstring=module_doc,
            line_number=1,
        )
    )

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            elements.extend(_analyse_class(node))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            elements.append(_analyse_function(node))

    return elements


def _analyse_class(node: ast.ClassDef) -> list[CodeElement]:
    """Analyse a class definition.

    arguments:
        `node: ast.ClassDef`
            AST class node

    returns: `list[CodeElement]`
        class element and all its methods
    """
    elements: list[CodeElement] = []
    class_doc = ast.get_docstring(node)

    # extract attributes from __init__ or class body
    attributes: list[tuple[str, str | None]] = []
    methods: list[CodeElement] = []

    for item in node.body:
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            if item.name == "__init__":
                attributes.extend(_extract_init_attributes(item))
            method = _analyse_function(item, class_name=node.name)
            methods.append(method)
        elif isinstance(item, ast.AnnAssign):
            attr_name = (
                item.target.id if isinstance(item.target, ast.Name) else ""
            )
            type_ann = _annotation_to_str(item.annotation)
            if attr_name:
                attributes.append((attr_name, type_ann))

    class_element = CodeElement(
        name=node.name,
        element_type="class",
        docstring=class_doc,
        line_number=node.lineno,
        attributes=attributes,
    )
    elements.append(class_element)
    elements.extend(methods)

    return elements


def _analyse_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_name: str | None = None,
) -> CodeElement:
    """Analyse a function definition.

    arguments:
        `node: ast.FunctionDef | ast.AsyncFunctionDef`
            AST function node
        `class_name: str | None = None`
            containing class name if this is a method

    returns: `CodeElement`
        function or method element
    """
    func_doc = ast.get_docstring(node)

    # extract arguments
    arguments: list[tuple[str, str | None, str | None]] = []

    # self/cls for methods
    if class_name and node.args.args:
        first_arg = node.args.args[0].arg
        if first_arg in ("self", "cls"):
            args_to_process = node.args.args[1:]
        else:
            args_to_process = node.args.args
    else:
        args_to_process = node.args.args

    for arg in args_to_process:
        arg_name = arg.arg
        type_ann = _annotation_to_str(arg.annotation)
        arguments.append((arg_name, type_ann, None))

    # handle defaults
    defaults_offset = len(node.args.args) - len(node.args.defaults)
    for i, default in enumerate(node.args.defaults):
        arg_idx = defaults_offset + i
        if arg_idx < len(arguments):
            name, type_ann, _ = arguments[arg_idx]
            default_val = _value_to_str(default)
            arguments[arg_idx] = (name, type_ann, default_val)

    # keyword-only arguments
    for arg in node.args.kwonlyargs:
        arg_name = arg.arg
        type_ann = _annotation_to_str(arg.annotation)
        arguments.append((arg_name, type_ann, None))

    # kwonly defaults
    for i, default_opt in enumerate(node.args.kw_defaults):
        if default_opt is not None:
            idx = len(node.args.args) + i
            if idx < len(arguments):
                name, type_ann, _ = arguments[idx]
                default_val = _value_to_str(default_opt)
                arguments[idx] = (name, type_ann, default_val)

    return_ann = _annotation_to_str(node.returns)
    element_type = "method" if class_name else "function"
    name = f"{class_name}.{node.name}" if class_name else node.name

    return CodeElement(
        name=name,
        element_type=element_type,
        docstring=func_doc,
        line_number=node.lineno,
        arguments=arguments,
        return_annotation=return_ann,
    )


def _extract_init_attributes(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, str | None]]:
    """Extract instance attributes from __init__ method.

    arguments:
        `node: ast.FunctionDef | ast.AsyncFunctionDef`
            __init__ method node

    returns: `list[tuple[str, str | None]]`
            list of (attribute_name, type_annotation) tuples
    """
    attributes: list[tuple[str, str | None]] = []

    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name):
                        if target.value.id == "self":
                            attributes.append((target.attr, None))
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Attribute):
                if isinstance(stmt.target.value, ast.Name):
                    if stmt.target.value.id == "self":
                        type_ann = _annotation_to_str(stmt.annotation)
                        attributes.append((stmt.target.attr, type_ann))

    return attributes


def _annotation_to_str(annotation: ast.expr | None) -> str | None:
    """Convert an AST annotation to a string.

    arguments:
        `annotation: ast.expr | None`
            AST annotation node

    returns: `str | None`
            string representation or None
    """
    if annotation is None:
        return None

    if isinstance(annotation, ast.Name):
        return annotation.id
    elif isinstance(annotation, ast.Constant):
        return repr(annotation.value)
    elif isinstance(annotation, ast.Attribute):
        parts: list[str] = []
        node: ast.expr = annotation
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    try:
        return ast.unparse(annotation)
    except Exception:
        return None


def _value_to_str(value: ast.expr) -> str | None:
    """Convert a value AST node to a string.

    arguments:
        `value: ast.expr`
            AST value node

    returns: `str | None`
            string representation or None
    """
    if isinstance(value, ast.Constant):
        return repr(value.value)
    elif isinstance(value, ast.Name):
        return value.id
    elif isinstance(value, ast.List):
        return "[]"
    elif isinstance(value, ast.Dict):
        return "{}"
    elif isinstance(value, ast.Tuple):
        return "()"

    try:
        return ast.unparse(value)
    except Exception:
        return None


class MDFValidator:
    """validates MDF docstrings against code elements.

    Compares parsed docstrings with actual code to detect mismatches.

    examples:
        ```python
        validator = MDFValidator(config)
        diagnostics = validator.validate_file(Path("src/main.py"))

        if diagnostics.has_errors():
            for diag in diagnostics:
                print(diag)
        ```
    """

    config: Config | None
    diagnostics: DiagnosticCollection

    def __init__(self, config: Config | None = None) -> None:
        """Initialise the validator.

        arguments:
            `config: Config | None = None`
                configuration for validation rules

        returns: `none`
            no return value
        """
        self.config = config
        self.diagnostics = DiagnosticCollection()

    def validate_file(self, file_path: Path) -> DiagnosticCollection:
        """Validate all docstrings in a file.

        arguments:
            `file_path: Path`
                path to the Python file

        returns: `DiagnosticCollection`
            collection of all diagnostics found
        """
        self.diagnostics = DiagnosticCollection()

        elements = analyse_file(file_path)
        if elements is None:
            self.diagnostics.add(
                Diagnostic(
                    code=ErrorCode.MALFORMED_MDF_DOCSTRING,
                    message=f"failed to parse {file_path}",
                    line=1,
                    column=0,
                )
            )
            return self.diagnostics

        for element in elements:
            self._validate_element(element)

        return self.diagnostics

    def _validate_element(self, element: CodeElement) -> None:
        """Validate a single code element's docstring.

        arguments:
            `element: CodeElement`
                element to validate

        returns: `none`
            no return value
        """
        if element.docstring is None:
            if self._should_have_docstring(element):
                self.diagnostics.add(
                    Diagnostic(
                        code=ErrorCode.MISSING_DOCSTRING,
                        message=f"missing docstring for {element.element_type} '{element.name}'",
                        line=element.line_number,
                        column=0,
                    )
                )
            return

        parser = MDFParser()
        parsed = parser.parse(element.docstring, element.line_number)

        for diag in parser.diagnostics:
            self.diagnostics.add(diag)

        if not parsed.is_mdf:
            self.diagnostics.add(
                Diagnostic(
                    code=ErrorCode.NOT_AN_MDF_DOCSTRING,
                    message=f"docstring for '{element.name}' is not in MDF format",
                    line=element.line_number,
                    column=0,
                )
            )
            return

        self._validate_against_code(parsed, element)

    def _should_have_docstring(self, element: CodeElement) -> bool:
        """Check if an element should have a docstring.

        arguments:
            `element: CodeElement`
                element to check

        returns: `bool`
            True if element should be documented
        """
        # skip private elements
        if element.name.startswith("_") and not element.name.startswith("__"):
            return False

        # skip special methods
        return not (
            element.element_type == "method"
            and element.name.split(".")[-1].startswith("__")
        )

    def _validate_against_code(
        self, parsed: ParsedDocstring, element: CodeElement
    ) -> None:
        """Validate parsed docstring against actual code.

        arguments:
            `parsed: ParsedDocstring`
                parsed docstring
            `element: CodeElement`
                code element to compare against

        returns: `none`
            no return value
        """
        if element.arguments:
            self._validate_arguments(parsed, element)

        if element.return_annotation:
            self._validate_return_type(parsed, element)

        if element.element_type == "class" and element.attributes:
            self._validate_attributes(parsed, element)

    def _validate_arguments(
        self, parsed: ParsedDocstring, element: CodeElement
    ) -> None:
        """Validate that arguments match between docstring and code.

        arguments:
            `parsed: ParsedDocstring`
                parsed docstring
            `element: CodeElement`
                code element with arguments

        returns: `none`
            no return value
        """
        args_section = None
        for section_type in (SectionType.ARGUMENTS, SectionType.PARAMETERS):
            args_section = parsed.get_section(section_type)
            if args_section:
                break

        if not args_section:
            if element.arguments:
                self.diagnostics.add(
                    Diagnostic(
                        code=ErrorCode.MISSING_INCOMING_SECTION,
                        message=f"missing arguments/parameters section for '{element.name}'",
                        line=element.line_number,
                        column=0,
                    )
                )
            return

        # get docstring parameter names
        doc_params: dict[str, ParameterDoc] = {}
        for item in args_section.items:
            if isinstance(item, ParameterDoc):
                doc_params[item.name] = item

        # get code argument names
        code_args = {arg[0] for arg in element.arguments}

        # check for extra parameters in docstring
        for param_name in doc_params:
            if param_name not in code_args:
                param = doc_params[param_name]
                line_num = (
                    param.location.line
                    if param.location
                    else element.line_number
                )
                self.diagnostics.add(
                    Diagnostic(
                        code=ErrorCode.EXTRA_FUNCTION_ARGUMENT_DECLARATION,
                        message=f"extra parameter '{param_name}' in docstring",
                        line=line_num,
                        column=0,
                    )
                )

        # check for missing parameters in docstring
        for arg_name, _, _ in element.arguments:
            if arg_name not in doc_params:
                self.diagnostics.add(
                    Diagnostic(
                        code=ErrorCode.MISSING_FUNCTION_ARGUMENT_DECLARATION,
                        message=f"missing parameter '{arg_name}' in docstring",
                        line=element.line_number,
                        column=0,
                    )
                )

    def _validate_return_type(
        self, parsed: ParsedDocstring, element: CodeElement
    ) -> None:
        """Validate return type annotation.

        arguments:
            `parsed: ParsedDocstring`
                parsed docstring
            `element: CodeElement`
                code element with return type

        returns: `none`
            no return value
        """
        returns_section = parsed.get_section(SectionType.RETURNS)

        if not returns_section and element.return_annotation:
            self.diagnostics.add(
                Diagnostic(
                    code=ErrorCode.MISSING_RETURNS_SECTION,
                    message=f"missing returns section for '{element.name}'",
                    line=element.line_number,
                    column=0,
                )
            )

    def _validate_attributes(
        self, parsed: ParsedDocstring, element: CodeElement
    ) -> None:
        """Validate class attributes.

        arguments:
            `parsed: ParsedDocstring`
                parsed docstring
            `element: CodeElement`
                class element with attributes

        returns: `none`
            no return value
        """
        attrs_section = parsed.get_section(SectionType.ATTRIBUTES)

        if not attrs_section and element.attributes:
            self.diagnostics.add(
                Diagnostic(
                    code=ErrorCode.MISSING_INCOMING_SECTION,
                    message=f"missing attributes section for class '{element.name}'",
                    line=element.line_number,
                    column=0,
                )
            )
            return

        if attrs_section:
            doc_attrs: set[str] = set()
            for item in attrs_section.items:
                if isinstance(item, ParameterDoc):
                    doc_attrs.add(item.name)

            code_attrs = {attr[0] for attr in element.attributes}

            # check for extra attributes
            for attr_name in doc_attrs:
                if attr_name not in code_attrs:
                    self.diagnostics.add(
                        Diagnostic(
                            code=ErrorCode.EXTRA_CLASS_ATTRIBUTE_DECLARATION,
                            message=f"extra attribute '{attr_name}' in docstring",
                            line=element.line_number,
                            column=0,
                        )
                    )

            # check for missing attributes
            for attr_name, _ in element.attributes:
                if attr_name not in doc_attrs:
                    self.diagnostics.add(
                        Diagnostic(
                            code=ErrorCode.MISSING_CLASS_ATTRIBUTE_DECLARATION,
                            message=f"missing attribute '{attr_name}' in docstring",
                            line=element.line_number,
                            column=0,
                        )
                    )
