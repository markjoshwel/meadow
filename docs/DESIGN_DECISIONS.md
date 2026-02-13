# Design Decisions

## Why Pure Functions Over Classes?

Many modules originally used classes with state (CodeAnalyzer, MDFValidator).
These have been refactored to pure functions because:

1. **Testability**: Pure functions are easier to test (input → output)
2. **Clarity**: No hidden state to track
3. **Composability**: Functions compose better than class instances
4. **Immutability**: Data flows in one direction

Exceptions remain as classes (dataclasses) for convenient attribute access.

## Exception Hierarchy Design

```
MeadowError (base)
├── ConfigError (configuration issues)
├── ParseError (docstring parsing failures)
├── ValidationError (validation failures)
└── GenerationError (docstring generation failures)
```

Each carries context:
- `location`: Where the error occurred
- `message`: Human-readable description
- `code`: ErrorCode enum value

## Type Safety Strategy

1. **No bare `Any`**: Every parameter and return has concrete type
2. **TypeVars for generics**: Properly constrained generic types
3. **NewType for distinctions**: `Markdown = NewType("Markdown", str)`
4. **Strict pyright**: basedpyright in strict mode

## Configuration Loading Order

1. `.meadoc.toml` (highest precedence)
2. `meadoc.toml`
3. `pyproject.toml` (lowest precedence)

This allows project-level overrides without modifying pyproject.toml.

## Pattern Matching vs if-elif chains

Python 3.13's `match` statement is used for:
- AST node type dispatch
- Error code categorisation
- Configuration value extraction

Benefits:
- Exhaustiveness checking (pyright can verify all cases handled)
- Cleaner syntax for complex conditions
- Better performance for many-branched logic

## Why MDF Over Existing Formats?

The meadow Docstring Format exists because:

1. **Plaintext first**: Readable without rendering
2. **Python syntax**: Uses actual Python type annotations
3. **Editor support**: Works across Zed, VS Code, PyCharm
4. **Simplicity**: No external dependencies for parsing

See README.md for full format specification.
