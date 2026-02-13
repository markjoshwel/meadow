# Meadow Hardening - Current Plan

## Status: In Progress

## Completed Tasks

### 1. Strict Type Safety (DONE)
- ✅ basedpyright: 0 errors
- ✅ mypy: 0 errors  
- ✅ ruff: 0 errors
- ✅ All tests pass (40/40)

### 2. Config Refactoring (IN PROGRESS)
**Moved `module_docstrings` from FormatConfig to top-level Config**

**Changes Made:**
- Added `module_docstrings: bool = False` to Config class
- Removed from FormatConfig class
- Updated config loading in `_load_from_file()` 
- Removed from `_load_format_config()`
- Updated `to_example_toml()` to output at top level
- Updated generator.py to use `config.module_docstrings`
- Updated tests to check Config.module_docstrings instead of FormatConfig.module_docstrings

**Files Modified:**
- src/meadow/config.py
- src/meadow/generator.py  
- tests/test_config.py

## Remaining Tasks

### 1. Module Docstring Checking (CRITICAL)
**Problem:** MDW101 errors still appear for module-level docstrings even with `module_docstrings = false`

**Root Cause:** The validator doesn't check the `module_docstrings` config setting before generating MDW101 errors.

**Location:** `src/meadow/validator.py` around line 394-402

**Current Code:**
```python
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
```

**Fix Needed:** Add check for `element.element_type == "module"` and `self.config.module_docstrings` before generating MDW101.

### 2. Document Private Functions (HIGH PRIORITY)
**User Request:** "include private functions just as a good documentation rule of thumb"

**Current Status:** 43 MDW101 errors remaining, many for private functions like:
- `_get_bool`, `_get_int`, `_get_str`, `_get_list`, `_get_table` (config.py)
- `_matches_exclude`, `_parse_gitignore`, `_matches_gitignore` (discovery.py)
- `_should_have_docstring`, `_validate_element`, etc. (validator.py)

**Approach:** 
- Run `meadoc format src/` to generate docstrings for these
- Review and improve the generated docstrings
- Consider updating `_should_have_docstring()` in validator to NOT skip private functions

### 3. MDF Parser Improvements (COMPLETED)
- ✅ Added "examples:" as alias for "usage:" section
- ✅ Fixed MDW309 (extra attribute '') bug by supporting examples section
- ✅ Fixed MDW325 by always generating returns sections
- ✅ Fixed MDW213 by ensuring correct section order

## Current Error Counts

```bash
# Type Checking
uv run basedpyright src/  # 0 errors
uv run mypy src/          # 0 errors
uv run ruff check src/    # 0 errors

# Tests
uv run pytest             # 40 passed

# MDF Compliance
uv run meadoc check src/  # 43 errors (mostly MDW101)
```

## MDF Error Breakdown (43 total)

### Module-level docstrings (11 errors)
- __init__.py, _version.py, config.py, discovery.py, errors.py, generator.py, main.py, markdown.py, parser.py, validator.py
- These should be suppressed when module_docstrings = false

### Private functions (need docstrings)
- config.py: _get_bool, _get_int, _get_str, _get_list, _get_table
- discovery.py: _matches_exclude, _parse_gitignore, _matches_gitignore  
- validator.py: Multiple _validate_* methods
- main.py: _add_common_args, _add_config_args

### Special methods
- DiagnosticCollection.__init__, __len__, __iter__
- Location.__str__, Diagnostic.__str__

## Files Needing Docstrings

### High Priority (Private functions)
1. `src/meadow/config.py` - _get_bool, _get_int, _get_str, _get_list, _get_table
2. `src/meadow/discovery.py` - _matches_exclude, _parse_gitignore, _matches_gitignore
3. `src/meadow/validator.py` - All _validate_* methods

### Medium Priority (Module level)
1. All `__init__.py` files
2. Module-level docstrings (if module_docstrings enabled)

## Next Steps

1. **Fix module_docstrings checking in validator.py**
   - Add config check before MDW101 for modules
   - Test that MDW101 disappears for modules when disabled

2. **Generate docstrings for private functions**
   - Run `meadoc format src/ --fix-malformed`
   - Review and improve generated docstrings
   - Ensure private functions are included in checking

3. **Update validator to not skip private functions**
   - Modify `_should_have_docstring()` 
   - Or ensure formatter generates docstrings for them

## Configuration

Current default config now includes at top level:
```toml
[meadoc]
# ... other options ...
module-docstrings = false  # Now shared across format/check/generate
```

## Key Insights

1. The formatter already generates docstrings for private functions (when run with --fix-malformed)
2. The validator skips private functions in `_should_have_docstring()`  
3. MDW101 is generated for ANY docstring that isn't MDF format, regardless of module_docstrings setting
4. Need to suppress MDW101 specifically for modules when module_docstrings=false

## Testing Checklist

- [ ] Module docstrings suppressed when module_docstrings=false
- [ ] Module docstrings checked when module_docstrings=true
- [ ] Private functions have proper docstrings
- [ ] All type checks pass
- [ ] All tests pass
- [ ] MDF check passes with 0 errors
