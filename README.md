# The meadow Docstring Format

_and, the [meadoc Docstring Machine](#the-meadoc-docstring-machine)_

a plaintext-first alternative documentation string style for Python

```python
class Cake(BaseModel):
    """
    a baker's confectionery, usually baked, a lie
    
    attributes:
        `name: str`
            name of the cake
        `ingredients: list[Ingredient]`
            ingredients of the cake
        `baking_duration: int`
            duration of the baking process in minutes
        `baking_temperature: int = 4000`
            temperature of the baking process in degrees kelvin
    """
    name: str
    ingredients: list[Ingredient]
    baking_duration: int
    baking_temperature: int = 4000
```

## the format

why another one? it's really just for me, but I think it's an okay-ish format

- it's easy and somewhat intuitive to read and write,
  especially because it's just plaintext

- it closely follows python syntax where it should,
  which includes type annotations

**(bonus!)** it works:

- best on Zed
- okay-ish Visual Studio Code
- eh on PyCharm

the format is comprised of multiple sections:

1. **preamble** \
    _a mandatory short one line description_

2. **body** \
    _an optional longer, potentially multi-line description_

3. **accepted (incoming) signatures** \
    _"attributes" for classes, "arguments" or "parameters" for functions_

    general format:

    ```text
    {attributes,arguments,parameters}:
        `<python variable declaration syntax>`
            <description>
    ```

4. **exported (outgoing) signatures** \
    _"functions" for module top-level docstrings, "methods" for class docstrings_

    general format:

    ```text
    {functions,methods}:
        `<python function declaration syntax without trailing colon>`
            <description of the function>
    ```

    example:

    ```text
    functions:
        `def bake(self, override: BakingOverride | None = None) -> bool`
            bakes the cake and returns True if successful
    ```

5. **returns** and **raises**

    general format, single type:

    ```text
    {returns,raises}: `<return type annotation>`
        <description>
    ```

    general format, multiple types:

    ```text
    {returns,raises}:
        `<first possible return type annotation/exception class>`
            <description>
        `<second possible return type annotation/exception class>`
            <description>
    ```

    examples:

    ```python
    def certain_unsafe_div(a: int | float, b: int | float) -> float:
        """
        divide a by b

        arguments:
            `a: int | float`
                numerator
            `b: int | float`
                denominator

        raises:
            `ZeroDivisionError`
                raised when denominator is 0
            `OverflowError`
                raised when the resulting number is too big
            `FloatingPointError`
                secret third thing

        returns: float
            the result, a divided by b
        """
        return a / b

    def uncertain_unsafe_read(path: Path) -> str:
        """
        blah blah helper blah

        arguments:
            `path: Path`
                path to read from

        raises: `Exception`
            god knows what path.read_text might raise

        returns: `str`
            the read out contents from the path
        """
        return path.read_text()
    ```

6. **usage** \
    _a markdown triple backtick block with usage examples_

    general format:

    ```markdown
    usage:
        ```python
        # ...
        ```
    ```

and are layed out as such:

1. start

    | section              | required |
    | -------------------- | -------- |
    | 1. `preamble`        | 🟢 yes   |
    | 2. `body` or `usage` | 🔴 no    |

2. details

    | section                             | required      |
    | ----------------------------------- | ------------- |
    | 3. `accepted (incoming) signatures` | 🟡 if present |
    | 4. `exported (outgoing) signatures` | 🟡 if present |
    | 5. `returns`                        | 🟡 if present |
    | 6. `raises`                         | 🟡 if present |

3. end

    | section              | required |
    | -------------------- | -------- |
    | 7. `body` or `usage` | 🔴 no    |

> **frequently questioned answers**
>
> > why do the `body` and `usage` sections appear multiple times
>
> because depending on your use case, you may have a postamble after the usage,
> or if your body is a postamble after the torso and knees section (and other
> similar use cases depending on reading flow)
>
> > what about custom text
>
> any other text will just be parsed as-is as body text, so there's no
> stopping you from adding an `example:` section (but cross-ide compatibility
> is finicky, especially with pycharm)
>
> > how does the parser detect sections
>
> the parser will only attempt compliance when matching a line with the
> following pattern:
>
> ```text
> {attributes,arguments,parameters,functions,methods,returns,raises,usage}:
> ```
>
> > what if a declaration is really long?
>
> you _could_ split the declaration into multiple lines, all within the same
> indentation level. but unless your function takes in dozens of arguments,
> a single-line declaration is preferred due to much wackier differences in
> lsp popover rendering strategies across different mainstream editors.
>
> ```text
> methods:
>     `def woah_many_argument_function(
>         ...
>     ) -> None`
>         blah blah blah blah blah blah
> ```

---

<!-- markdownlint-disable single-h1 -->

# The meadoc Docstring Machine

<!-- markdownlint-enable -->

a docstring machine based on typing information for the [meadow Docstring Format](#the-meadow-docstring-format)

use [uvx](https://docs.astral.sh/uv/guides/tools/), to quickly try it out.

or use pip install, pipx install, or other package managers to install `meadoc`.

```text
$ uvx meadoc
meadoc: a docstring machine based on typing information

usage:
  meadoc format [source, ...]      generate or update docstrings in files
  meadoc check [source, ...]       lint files for docstring issues
  meadoc generate [source, ...]    generate markdown api references
  meadoc config                    display docs about configuration
  meadoc about                     display docs about the meadow Docstring Format

run 'meadoc <command> --help' for more information on a specific command
```

## command line usage

### meadoc format

**usage:**

```text
meadoc format [source ...]
              [--fix-malformed]
              [--custom-todoc-message CUSTOM_TODOC_MESSAGE]
              [--ignore IGNORE]
```

- `--fix-malformed` \
    flag to fix any fixable malformed MDF docstrings automatitcally

- `--custom-todoc-message CUSTOM_TODOC_MESSAGE` \
    specify a string to use anything other than `# TODOC: meadoc` when
    meadoc finds a non-MDF compliant or missing docstring 

- (see [shared arguments](#shared-arguments) for the format,
    check and generate subcommands)

**example output:**

<!-- markdownlint-disable line-length -->
```text
src/meadow/ignore.py: generated 1 new docstring, updated 1 docstring, and skipped 1 malformed docstring
src/meadow/main.py: updated 3 docstrings
src/meadow/common.py: all 12 relevant docstrings are compliant
```
<!-- markdownlint-enable -->

**behaviour:**

1. [resolve sources](#source-argument-resolution)

2. gather all docstrings, adding a TODOC message is a docstring is missing
    where there should be one (if it's not private, etc)

3. check all docstrings for MDF compliance and completeness

4. docstrings that resemble the MDF format, but are incorrectly written,
    or are outdated, are considered malformed. and if `--fix-malformed` was
    passed, will be fixed

5. docstrings that resemble other mainstream docstring formats will be
    converted to MDF

6. docstrings that are not a known format will be considered preamble and body
    text, and will be used for generating an MDF docstring

7. a summary of the files and the number of docstrings processed are printed
    to stdout

8. exits with code 0, else will exit with a code corresponding to the number
    point of this behaviour list

### meadoc check

**usage:**

```text
meadoc check [source ...]
```

- (see [shared arguments](#shared-arguments) for the format,
    check and generate subcommands)

**behaviour:**

1. [resolve sources](#source-argument-resolution)

2. gather all docstrings, noting an issue if a docstring is missing
    where there should be one (if it's not private, etc)

3. check all docstrings for MDF compliance and completeness

4. docstrings that resemble the MDF format, but are incorrectly written,
    or are outdated, are considered malformed, and are noted as issues

5. docstrings that resemble other mainstream docstring formats will be noted
    as issues

6. docstrings that are not a known format, probably plaintext, will be noted
    as issues

7. a summary of the per-line issues are printed to stderr

8. exits with code 0 if no issues were found, else will exit with 1

### meadoc generate

**usage:**

```text
meadoc generate [source ...] [-o --output FILE]
              [-H --starting-header N]
              [--no-toc]
```

- `-o --output FILE` \
    specify a file path to output the generated markdown file into;
    else output to stdout

- `-H --starting-header N` \
    set the starting header level for the api reference title (default: 2)
    - `2`: h2="api reference", h3=module, h4=class/function
    - `3`: h3="api reference", h4=module, h5=class/function

- `--no-toc` \
    disable table of contents generation (enabled by default)

- (see [shared arguments](#shared-arguments) for the format,
    check and generate subcommands)

**behaviour:**

1. [resolve sources](#source-argument-resolution)

2. gather meadow-compliant docstrings, skipping non-compliant or malformed
    docstrings

3. convert into markdown

4. any found non-compliant docstrings are skipped, but counted to be printed
    as a warning to stderr

5. exits with code 0, else will exit with a code corresponding to the number
    point of this behaviour list

### meadoc config

**usage:**

```text
meadoc config [pyproject.toml | meadoc.toml]
```

**behaviour:**

1. if no arguments are provided, prints the documentation about
    [configuration](#configuration) to stdout

2. if either "pyproject.toml" or "meadoc.toml" were provided as a subcommand,
    print the appropriate example configuration

    - if "pyproject.toml" was provided, the parent toml table is `[tool.meadow]`

    - if "meadoc.toml" was provided, the parent toml table is `[meadow]`

    - if configuration options were passed in, like `--exclude`, the printed
      configuration will be updated with the provided values

3. exits with code 0

### meadoc about

**usage:**

```text
meadoc about
```

**behaviour:**

1. prints the documentation about [the format](#the-format) to stdout
2. exits with code 0

### source argument resolution

1. if no `source` arguments are provided, meadoc will
    [recursively search for python files](#directory-traversal-and-file-finding)
    in the current directory.

2. if `source` arguments were provided, meadoc will then use the provided
    files. but if any argument is a directory, meadoc will
    [recursively search for python files](#directory-traversal-and-file-finding)
    in that directory.

### shared arguments

```text
meadoc {format,check,generate} [--include INCLUDE]
                               [--exclude EXCLUDE]
                               [-n, --ignore-no-docstring]
                               [-o, --ignore-outdated]
                               [-m, --ignore-malformed]
                               [-d, --disrespect-gitignore]
                               [-p, --plumbing]
```

- `--include INCLUDE` \
    a glob pattern to include files in the search.
    replaces default search patterns defined in the config

- `--exclude EXCLUDE` \
    a glob pattern to exclude files from the search

- `-n --ignore-no-docstring` \
    don't format, check and warn, or generate docs from files without docstrings \
    (this option is redundant for the `generate` subcommand)

- `-o --ignore-outdated` \
    don't format, check and warn, or generate docs from files that are outdated \
    (this option is redundant for the `generate` subcommand)

- `-m --ignore-malformed` \
    don't format, check and warn, or generate docs from files that are malformed \
    (this option is redundant for the `generate` subcommand)

- `-d --disrespect-gitignore` \
    disable respecting `.gitignore` files when searching for python files

- `-p --plumbing` \
    respond in json, for scripting and automation

### directory traversal and file finding

to implement this, i use my shared
[libsightseeing](https://github.com/markjoshwel/RaiseAttention/tree/main/src/libsoulsearching)
library.

1. when meadoc doesn't know where to find python files, it will recursively
    search for python files in the current directory.

    if a directory is provided as one of the `source` arguments, meadoc will
    recursively search for python files in that directory.

2. if `respect-gitignore` is set to `true` in meadoc's configuration, which
    it is by default, meadoc will respect `.gitignore` files when searching
    for python files.

    disabling this on a per-invocation basis is possible by passing
    `--disrespect-gitignore` or `-d` in the command line.

    this means that meadoc will attempt to find a .gitignore file in the
    current **and** any parent directories, to respect repository-wide
    gitignore rules.

    during the recursive search, it will also use the .gitignore files in the
    traversed directories, respecting more localised gitignore rules.

    if this breaks any workflows, please consider specifying `include` and
    `exclude` patterns either via command line arguments or configuration
    files.

## configuration

> **heads up** \
> this is readable with `meadoc config`

this is attempt to be loaded from:

1. `.meadoc.toml`
2. `meadoc.toml`
3. `pyproject.toml` (use `[tool.meadoc]` instead of `[meadoc]`)

```toml
# the default configuration for meadoc, a docstring machine based on typing
# information for the meadow Docstring Format
# 
# all available configuration keys are exposed here with their defaults,
# alongside comments to explain what they do, and what values they accept

[meadoc]
# source file resolution
# glob patterns to include/exclude/ignore files and directories
include = [
    # "src/**/*.py",
    # "tests/**/*.py",
]
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pyenv",
    ".pytest_cache",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    ".vscode",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
]

# meadoc will by default respect .gitignores when looking for python files
# especially when no sources are specified, e.g. running `meadoc check`
# without arguments in the project root
respect-gitignore = true

multi-line-summary-on-line = 2
# options: 1 or 2, change to 1 for strict PEP 257 compliance
# 
# multi-line-summary-on-line = 1
# > """preamble
# > 
# > body
# > """
# 
# multi-line-summary-on-line = 2
# > """
# > preamble
# > 
# > body
# > """

[meadoc.format]
# module docstrings usually have more varied styling/writing,
# so it is disabled by default
module-docstrings = false

# docstring formatting preferences
line-length = 79
line-ending = ""  # empty = autodetect
indent-width = 4
indent-style = "space"  # or 'tabs'

# any detected python code blocks can be formatted with a command of your choice
# skip on a docstring-by-docstring basis with `# meadow: ignore[codeBlockFormat]`
code-block-format = true
code-block-format-command = ["ruff", "format", "-"]

[meadoc.generate]
external-link-reference = "meadoc.toml"

# markdown formatting preferences
line-length = 79
line-ending = ""  # empty = autodetect
indent-width = 4
indent-style = "space"  # or 'tabs'

# header level configuration
starting-header-level = 2  # 1-6, sets h2="api reference" by default
include-toc = true  # set to false to disable table of contents

[meadoc.generate.external-links]
# this is not actually included with the default configuration,
# but an example of how external links would be configured.
#
# on running `meadoc format` or `meadoc check`, any third party modules
# encountered will be noted down here, allowing you to add links to them if
# you would want clickable links in the generated markdown.
"tomlkit.TOMLDocument" = "https://tomlkit.readthedocs.io/en/latest/api/#tomlkit.TOMLDocument"
```

## errors

you can tune what errors are reported either by:

1. using [command line arguments](#command-line-usage)

2. using [configuration files](#configuration)

3. a `# meadow: ignore` comment placed right after the docstring

    for more precise error ignoring:
    `# meadow: ignore[<comma separated code or name>]`

    example:

    ```python
    def example() -> None:
        """blah
        blah
        blah"""  # meadow: ignore[invalidDocstring]

### list of errors

- `MDW100` missingDocstring \
  noted when there is no docstring attached to a function, class, or module
  - `MDW101` notAnMdfDocstring \
    noted when the docstring is not an MDF docstring at all
  - `MDW102` otherFormatDocstring \
    noted when the docstring is a mainstream docstring format
    (sphinx, google) but not the meadow Docstring Format

- `MDW200` malformedMdfDocstring
  - `MDW201` missingPreamble
  - `MDW202` invalidClassDeclaration
  - `MDW203` invalidClassAttributeDeclaration
  - `MDW204` invalidFunctionDeclaration
  - `MDW205` invalidFunctionArgumentDeclaration
  - `MDW206` invalidVariableDeclaration
  - `MDW207` invalidReturnTypeAnnotation
  - `MDW208` unknownRaisesClass
  - `MDW209` missingBackticks
  - `MDW210` misspelledSectionName
  - `MDW211` missingSectionColon
  - `MDW212` invalidIndentation
  - `MDW213` sectionsOutOfOrder
  - `MDW214` multiLineSummaryFirstLine
  - `MDW215` multiLineSummarySecondLine
  - `MDW216` incompleteMdfDocstring
  - `MDW217` duplicateClassDeclaration
  - `MDW218` duplicateClassAttributeDeclaration
  - `MDW219` duplicateFunctionDeclaration
  - `MDW220` duplicateFunctionArgumentDeclaration
  - `MDW221` duplicateVariableDeclaration
  - `MDW222` duplicateReturnTypeAnnotation
  - `MDW223` duplicateRaisesClass

- `MDW300` outdatedMdfDocstring
  - `MDW301` outdatedClassDeclaration
  - `MDW302` outdatedClassAttributeDeclaration
  - `MDW303` outdatedFunctionDeclaration
  - `MDW304` outdatedFunctionArgumentDeclaration
  - `MDW306` outdatedVariableDeclaration
  - `MDW305` outdatedReturnTypeAnnotation
  - `MDW307` outdatedRaisesClass
  - `MDW308` extraClassDeclaration
  - `MDW309` extraClassAttributeDeclaration
  - `MDW310` extraFunctionDeclaration
  - `MDW311` extraFunctionArgumentDeclaration
  - `MDW312` extraVariableDeclaration
  - `MDW313` extraReturnTypeAnnotation
  - `MDW314` extraRaisesClass
  - `MDW315` missingClassDeclaration
  - `MDW316` missingClassAttributeDeclaration
  - `MDW317` missingFunctionDeclaration
  - `MDW318` missingFunctionArgumentDeclaration
  - `MDW319` missingVariableDeclaration
  - `MDW320` missingReturnTypeAnnotation
  - `MDW321` missingRaisesClass
  - `MDW322` missingPreambleSection
  - `MDW323` missingIncomingSection
  - `MDW324` missingOutgoingSection
  - `MDW325` missingReturnsSection
  - `MDW326` missingRaisesSection
