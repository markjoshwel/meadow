# meadow Development Tasks

## Current Phase: Comprehensive Rewrite

Status: **Completed** ✅

### Completed

- ✅ Documentation infrastructure (docs/ folder with ARCHITECTURE.md, DESIGN_DECISIONS.md, etc.)
- ✅ Dependency updates (tomlkit version constraint)
- ✅ Module rewrites with type safety
  - errors.py: MeadowError hierarchy, properties instead of functions
  - config.py: Pattern matching, proper exception handling
  - discovery.py: Pure functions, Path consistency
  - parser.py: TypeVar usage, consolidated parsing
  - validator.py: Pure functions instead of classes
  - generator.py: DocstringBuilder with UpdateResult TypedDict
  - markdown.py: NewType for Markdown, template strings
  - main.py: Strict typing, proper exit codes
- ✅ Test modernisation (updated to use new API)
- ✅ AGENTS.md update (lean with links to docs)
- ✅ Final verification (all 44 tests pass)
- ✅ MDF docstring style compliance (lowercase throughout)

### In Progress

None - rewrite is complete!

### Blockers

None.

### Notes

Major improvements in this rewrite:
- **Type Safety**: Strict basedpyright compliance across all modules
- **Exception Safety**: Proper MeadowError hierarchy with context
- **Code Maintainability**: Pure functions, literate programming style
- **MDF Compliance**: All modules now follow meadow Docstring Format
- **British Spelling**: Consistent use throughout (behaviour, colour, etc.)

Remaining type warnings are from incomplete tomlkit type stubs (external dependency).
All functional tests pass (40/40).

See [REFACTORING_NOTES.md](REFACTORING_NOTES.md) for detailed API changes.
