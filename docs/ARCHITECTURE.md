# meadow Architecture

## Module Dependency Graph

```
errors.py (foundation)
    ↓
config.py
    ↓
discovery.py → config, errors
    ↓
parser.py → errors
    ↓
validator.py → config, errors, parser
    ↓
generator.py → config, validator, errors
    ↓
markdown.py → config, parser, validator
    ↓
main.py → all modules
```

## Module Responsibilities

### `errors.py`
Foundation module defining:
- `MeadowError` (base exception class)
- `ErrorCode` (enum of all diagnostic codes)
- `ErrorSeverity` (WARNING, ERROR, INFO)
- `Diagnostic` (individual error instance)
- `DiagnosticCollection` (aggregate errors)
- `Location` (file:line:column tracking)

No external dependencies.

### `config.py`
Configuration management:
- `Config` (main configuration dataclass)
- `FormatConfig` (format subcommand settings)
- `GenerateConfig` (generate subcommand settings)
- Loading from TOML files (pyproject.toml, meadoc.toml, .meadoc.toml)
- Default pattern definitions

Depends on: errors (for ConfigError)

### `discovery.py`
File system discovery:
- `discover_python_files()` (thin wrapper around libsightseeing)

Uses libsightseeing for gitignore support and pattern matching.

### `parser.py`
MDF docstring parsing:
- `parse_docstring()` (main entry point)
- `MDFParser` (parser state machine)
- `ParsedDocstring` (result structure)
- Section types: PREAMBLE, BODY, ATTRIBUTES, ARGUMENTS, etc.
- Type detection (sphinx, google format recognition)

Uses dataclasses for AST-like representation.

### `validator.py`
Validation against actual code:
- `analyse_file()` (pure function) - extracts `CodeElement` info from Python files
- `CodeElement` (dataclass with extracted code info)
- `MDFValidator` (class with `validate_file()` method)
- Cross-reference docstring with AST

Uses Python's `ast` module for code analysis.

### `generator.py`
Docstring generation:
- `DocstringGenerator` (generation logic)
- `DocstringUpdater` (file modification)
- Template-based string building
- Preservation of existing preamble/body

### `markdown.py`
Markdown API documentation:
- `MarkdownGenerator` (markdown output)
- Template strings for consistent formatting
- External link resolution

### `main.py`
CLI entry point:
- `create_parser()` (argparse setup)
- Command handlers: `cmd_format()`, `cmd_check()`, etc.
- Exit code management
- Error handling and reporting

## Design Principles

1. **Pure Functions Preferred**: Where possible, use pure functions instead
   of stateful classes. This improves testability and reduces side effects.

2. **Type Safety**: All public APIs have explicit type annotations. Use
   `typing` module features appropriately.

3. **British Spelling**: All documentation and code uses British English
   (behaviour, colour, initialise, etc.)

4. **Exception Hierarchy**: All errors inherit from `MeadowError` for
   consistent catching and handling.

5. **Literate Programming**: Code is self-documenting with MDF docstrings.
   Complex logic has explanatory comments.

## Data Flow

```
CLI Input
    ↓
Argument Parsing (main.py)
    ↓
Config Loading (config.py)
    ↓
File Discovery (discovery.py)
    ↓
For each file:
    - Parse Python AST (validator.py)
    - Parse Docstrings (parser.py)
    - Validate (validator.py)
    - Generate/Update (generator.py)
    - Output Markdown (markdown.py)
    ↓
Report Results (main.py)
```
