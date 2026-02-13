# Exception Strategy

## Exception Hierarchy

```
Exception
└── MeadowError (meadow base)
    ├── ConfigError (configuration issues)
    │   └── ConfigFileNotFoundError
    │   └── ConfigParseError
    │   └── ConfigValidationError
    ├── ParseError (docstring parsing failures)
    │   └── InvalidSectionError
    │   └── MalformedDocstringError
    ├── ValidationError (validation failures)
    │   └── MissingDocstringError
    │   └── OutdatedDocstringError
    └── GenerationError (docstring generation failures)
        └── FileWriteError
```

## Design Principles

1. **Context-Rich**: Every exception carries location (file, line, column)
2. **Actionable Messages**: Error messages suggest fixes
3. **Hierarchical**: Catch `MeadowError` for all meadow-specific issues
4. **Non-Fatal by Default**: Parser/validator continue after errors

## Usage Patterns

### Catching All Meadow Errors

```python
from meadow.errors import MeadowError

try:
    result = process_file(path)
except MeadowError as exc:
    print(f"meadow error at {exc.location}: {exc.message}")
```

### Specific Error Handling

```python
from meadow.errors import ConfigError, ParseError

try:
    config = Config.load(path)
except ConfigFileNotFoundError:
    # Use defaults
    config = Config.default()
except ConfigParseError as exc:
    # Report syntax error
    print(f"Config syntax error: {exc.message}")
```

### Error Context

All exceptions provide:

```python
exc.message      # Human-readable description
exc.location     # Location (file, line, column) or None
exc.code         # ErrorCode enum (for validation errors)
exc.__str__()    # Formatted: "path:line:col: message"
```

## Exit Codes

CLI uses these exit codes:

- `0`: Success
- `1`: Usage error (bad arguments)
- `2`: Configuration error
- `3`: Parse error
- `4`: Validation error
- `5`: Generation error
- `255`: Unexpected error

## Error Messages

Follow the format: `meadow: severity: message`

Examples:
```
meadow: error: missing preamble in docstring at src/main.py:42:0
meadow: warning: outdated argument 'old_param' at src/lib.py:15:8
```
