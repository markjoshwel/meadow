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
uv run basedpyright src scripts

# general linting
uv run ruff check .

# type safety
uv run mypy .

# exception safety
uv run raiseattention check src

# MDF compliance (self-check)
uv run meadoc check src
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
├── stdlib_links.py   # Baked-in standard library doc URLs
├── validator.py      # Validation against code
├── generator.py      # Docstring generation
├── markdown.py       # Markdown API doc generation
└── main.py           # CLI entry point
```

## Current Status

Comprehensive rewrite **completed** and ready for publication:
- ⚠️ Type safety (4 basedpyright errors in markdown.py due to incomplete tomlkit type stubs)
- ✅ Exception safety (MeadowError hierarchy)
- ✅ MDF docstring compliance (self-check passes)
- ✅ Code maintainability improvements
- ✅ Test modernisation complete (39 tests passing)
- ✅ Baked-in stdlib documentation links (252 modules)
- ✅ External link auto-discovery for third-party types
- ✅ Version 2026.2.15 tagged and ready
