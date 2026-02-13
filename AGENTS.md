# Agent Context

## Quick Start

This is meadow: a docstring machine based on typing information for the meadow Docstring Format (MDF).

- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module overview and dependencies
- See [docs/TODO.md](docs/TODO.md) for current work status
- See [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md) for rationale behind key choices
- See [docs/EXCEPTION_STRATEGY.md](docs/EXCEPTION_STRATEGY.md) for error handling patterns
- See [docs/REFACTORING_NOTES.md](docs/REFACTORING_NOTES.md) for breaking changes from previous versions

## Running Checks

```bash
# strict static analysis + type check
uv run basedpyright .

# type safety
uv run mypy .

# exception safety
uvx --refresh --from B:\RaiseAttention raiseattention check .

# MDF compliance (self-check)
uvx --refresh --from B:\meadow meadoc check .
```

## Code Standards

- British English: behaviour, colour, initialise, etc.
- MDF docstrings required for all public APIs
- Explicit types, minimal use of `Any`
- All errors inherit from `MeadowError`
- Pure functions preferred over stateful classes
- Python 3.13+ features (match statements, new typing)

## Module Structure

```
src/meadow/
├── __init__.py       # Package entry, version
├── _version.py       # Version constant
├── errors.py         # Exceptions, diagnostics, error codes
├── config.py         # Configuration loading (toml)
├── discovery.py      # File discovery, gitignore support
├── parser.py         # MDF docstring parser
├── validator.py      # Validation against code
├── generator.py      # Docstring generation
├── markdown.py       # Markdown API doc generation
└── main.py           # CLI entry point
```

## Current Status

Comprehensive rewrite in progress:
- ✅ Type safety (strict basedpyright compliance)
- ✅ Exception safety (MeadowError hierarchy)
- ✅ MDF docstring compliance
- ✅ Code maintainability improvements
- 🔄 Tests modernisation in progress
