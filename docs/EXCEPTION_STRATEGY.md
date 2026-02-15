# Exception Strategy

## Exception Hierarchy

```
Exception
└── MeadowError (meadow base)
    ├── ConfigError (configuration issues)
    ├── ParseError (docstring parsing failures)
    ├── ValidationError (validation failures)
    └── GenerationError (docstring generation failures)
```

All meadow exceptions inherit from `MeadowError` and carry context.

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
except ConfigError as exc:
    # Handle configuration issues
    print(f"Config error: {exc.message}")
```

### Error Context

All exceptions provide:

```python
exc.message      # Human-readable description
exc.location     # Location (file, line, column) or None
exc.__str__()    # Formatted: "path:line:col: message"
```

## Error Reporting Format

Error messages follow the format: `program: level: message`

Examples:
```
meadow: error: missing preamble in docstring at src/main.py:42:0
meadow: warning: outdated argument 'old_param' at src/lib.py:15:8
```

## Error Codes

The `ErrorCode` enum provides specific codes for different issues:
- MDW1xx: Missing docstring issues
- MDW2xx: Malformed docstring issues  
- MDW3xx: Outdated docstring issues

See `errors.py` for the full list.
