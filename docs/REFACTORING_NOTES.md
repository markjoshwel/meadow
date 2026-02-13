# Refactoring Notes

## Breaking Changes

This rewrite introduces breaking changes from the previous (unreleased) version.

### Exception Handling

**Before**: Used built-in exceptions with string messages
**After**: All exceptions inherit from `MeadowError`

Migration:
```python
# Old
raise ValueError("Invalid config")

# New
raise ConfigError("Invalid config", location=Location(1, 0, "config.py"))
```

### API Changes

#### `errors.py`

- **Removed**: `get_error_severity()` and `get_error_description()` free functions
- **Added**: `ErrorCode.severity` property and `ErrorCode.description` property

#### `config.py`

- **Removed**: Helper functions `_get_str`, `_get_bool`, `_get_int`, etc.
- **Added**: Pattern matching in `_load_from_table()`
- **Changed**: `Config.load()` now returns `Config | None` instead of always Config

#### `discovery.py`

- **Removed**: Class-based `FileDiscovery`
- **Added**: Pure functions `discover_python_files()`, `should_process_file()`
- **Changed**: Returns `list[Path]` instead of iterator (simpler type)

#### `parser.py`

- **Removed**: Separate `_parse_parameters`, `_parse_functions`, etc.
- **Added**: Generic `_parse_section_items()` with TypeVar
- **Changed**: `parse_docstring()` now raises `ParseError` on invalid input

#### `validator.py`

- **Removed**: `CodeAnalyzer` class with state
- **Added**: `analyse_file()` pure function returning `list[CodeElement]`
- **Removed**: `MDFValidator` class
- **Added**: `validate_element()` pure function

#### `generator.py`

- **Removed**: Separate `DocstringGenerator` and `DocstringUpdater` classes
- **Added**: Single `DocstringBuilder` class with clear lifecycle

#### `markdown.py`

- **Added**: `Markdown = NewType("Markdown", str)` for type distinction
- **Changed**: Template-based string building

#### `main.py`

- **Added**: TypedDict for argparse namespace
- **Changed**: Command handlers return `Result` type instead of bare int

## File Structure Changes

None. All files remain in `src/meadow/`.

## Behavioural Changes

### Stricter Type Checking

Previously many `type: ignore` comments suppressed errors. These are now
fixed with proper types.

### More Specific Exceptions

File operations now raise specific exceptions instead of generic `Exception`:
- `ConfigError` for configuration issues
- `ParseError` for parsing failures
- `ValidationError` for validation failures

### Consistent Return Types

Functions that previously returned `Any` now return concrete types:
- `ast.parse()` results are properly typed
- Configuration values are validated at load time

## Testing Changes

Tests updated to:
1. Use type annotations
2. Use British spelling
3. Check for specific exception types
4. Use structured assertions instead of string contains
