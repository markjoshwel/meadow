"""meadow: a docstring machine based on typing information.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

main entry point for the meadoc command-line interface.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from meadow._version import __version__
from meadow.config import Config, find_project_root
from meadow.discovery import discover_python_files
from meadow.errors import ErrorSeverity
from meadow.generator import DocstringUpdater
from meadow.markdown import MarkdownGenerator
from meadow.validator import MDFValidator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for meadoc."""
    parser = argparse.ArgumentParser(
        prog="meadoc",
        description="a docstring machine based on typing information for the meadow Docstring Format",
    )

    _ = parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="available commands"
    )

    # format command
    format_parser = subparsers.add_parser(
        "format",
        help="generate or update docstrings in files",
    )
    _add_common_args(format_parser)
    _ = format_parser.add_argument(
        "--fix-malformed",
        action="store_true",
        help="fix any fixable malformed MDF docstrings automatically",
    )
    _ = format_parser.add_argument(
        "--custom-todoc-message",
        type=str,
        default="# TODOC: meadoc",
        help="string to use for TODOC comments",
    )

    # check command
    check_parser = subparsers.add_parser(
        "check",
        help="lint files for docstring issues",
    )
    _add_common_args(check_parser)

    # generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="generate markdown api references",
    )
    _add_common_args(generate_parser)
    _ = generate_parser.add_argument(
        "-O",
        "--output",
        type=str,
        help="output file path (default: stdout)",
    )
    _ = generate_parser.add_argument(
        "-H",
        "--starting-header",
        type=int,
        choices=range(1, 7),
        default=2,
        metavar="N",
        help="starting header level for api reference title (default: 2)",
    )
    _ = generate_parser.add_argument(
        "--no-toc",
        action="store_true",
        help="disable table of contents generation",
    )

    # config command
    config_parser = subparsers.add_parser(
        "config",
        help="display docs about configuration",
    )
    _ = config_parser.add_argument(
        "config_type",
        nargs="?",
        choices=["pyproject.toml", "meadoc.toml"],
        help="print example configuration for the specified file type",
    )
    _add_config_args(config_parser)

    # about command
    _ = subparsers.add_parser(
        "about",
        help="display docs about the meadow Docstring Format",
    )

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a subparser."""
    _ = parser.add_argument(
        "source",
        nargs="*",
        type=Path,
        help="source files or directories to process",
    )
    _ = parser.add_argument(
        "--include",
        type=str,
        action="append",
        help="glob pattern to include files",
    )
    _ = parser.add_argument(
        "--exclude",
        type=str,
        action="append",
        help="glob pattern to exclude files",
    )
    _ = parser.add_argument(
        "-n",
        "--ignore-no-docstring",
        action="store_true",
        help="ignore files without docstrings",
    )
    _ = parser.add_argument(
        "-o",
        "--ignore-outdated",
        action="store_true",
        help="ignore files with outdated docstrings",
    )
    _ = parser.add_argument(
        "-m",
        "--ignore-malformed",
        action="store_true",
        help="ignore files with malformed docstrings",
    )
    _ = parser.add_argument(
        "-d",
        "--disrespect-gitignore",
        action="store_true",
        help="disable respecting .gitignore files",
    )
    _ = parser.add_argument(
        "-p",
        "--plumbing",
        action="store_true",
        help="output in json format for scripting",
    )


def _add_config_args(parser: argparse.ArgumentParser) -> None:
    """Add config-specific arguments."""
    _ = parser.add_argument(
        "--include",
        type=str,
        action="append",
        help="set include pattern in example config",
    )
    _ = parser.add_argument(
        "--exclude",
        type=str,
        action="append",
        help="set exclude pattern in example config",
    )


def cmd_format(args: argparse.Namespace) -> int:
    """Handle the format command."""
    config = Config.load()

    # update config from args
    if args.include:
        config.include = args.include
    if args.exclude:
        config.exclude.extend(args.exclude)

    # discover files
    files = list(
        discover_python_files(
            args.source,
            config,
            respect_gitignore=not args.disrespect_gitignore,
        )
    )

    if not files:
        if args.plumbing:
            print(json.dumps({"files": [], "summary": "no files found"}))
        else:
            print("no files found")
        return 0

    # process files
    updater = DocstringUpdater(config)
    results: list[dict[str, Any]] = []

    for file_path in files:
        update_result = updater.update_file(
            file_path, fix_malformed=args.fix_malformed
        )
        file_result: dict[str, Any] = dict(update_result)
        file_result["file"] = str(file_path)
        results.append(file_result)

    # output results
    if args.plumbing:
        print(json.dumps({"files": results}))
    else:
        for result in results:
            file_str = result["file"]
            parts: list[str] = []
            if result["generated"]:
                parts.append(
                    f"generated {result['generated']} new docstring(s)"
                )
            if result["updated"]:
                parts.append(f"updated {result['updated']} docstring(s)")
            if result["skipped"]:
                parts.append(f"skipped {result['skipped']} docstring(s)")
            if result["malformed"]:
                parts.append(
                    f"found {result['malformed']} malformed docstring(s)"
                )

            if parts:
                print(f"{file_str}: {', '.join(parts)}")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Handle the check command."""
    config = Config.load()

    # update config from args
    if args.include:
        config.include = args.include
    if args.exclude:
        config.exclude.extend(args.exclude)

    # discover files
    files = list(
        discover_python_files(
            args.source,
            config,
            respect_gitignore=not args.disrespect_gitignore,
        )
    )

    if not files:
        if args.plumbing:
            print(
                json.dumps(
                    {"files": [], "issues": [], "summary": "no files found"}
                )
            )
        else:
            print("no files found")
        return 0

    # validate files
    validator = MDFValidator(config)
    all_issues: list[dict[str, Any]] = []
    has_errors = False

    for file_path in files:
        diagnostics = validator.validate_file(file_path)

        for diag in diagnostics:
            issue = {
                "file": str(file_path),
                "line": diag.line,
                "column": diag.column,
                "code": diag.code.value,
                "message": diag.message,
                "severity": diag.severity.name if diag.severity else "ERROR",
            }
            all_issues.append(issue)

            if diag.severity == ErrorSeverity.ERROR:
                has_errors = True

    # output results
    if args.plumbing:
        print(
            json.dumps(
                {"files": [str(f) for f in files], "issues": all_issues}
            )
        )
    else:
        for issue in all_issues:
            print(
                f"{issue['file']}:{issue['line']}:{issue['column']}: "
                f"{issue['code']}: {issue['message']}"
            )

    return 1 if has_errors else 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Handle the generate command."""
    config = Config.load()

    # update config from args
    if args.include:
        config.include = args.include
    if args.exclude:
        config.exclude.extend(args.exclude)

    # update generate config from CLI args
    config.generate.starting_header_level = args.starting_header
    if args.no_toc:
        config.generate.include_toc = False

    # discover files
    files = list(
        discover_python_files(
            args.source,
            config,
            respect_gitignore=not args.disrespect_gitignore,
        )
    )

    if not files:
        if args.plumbing:
            print(
                json.dumps(
                    {"files": [], "markdown": "", "summary": "no files found"}
                )
            )
        else:
            print("no files found")
        return 0

    # generate markdown
    generator = MarkdownGenerator(config.generate)
    base_path = find_project_root()
    markdown = generator.generate_for_files(files, base_path)

    # output results
    if args.plumbing:
        print(
            json.dumps(
                {"files": [str(f) for f in files], "markdown": markdown}
            )
        )
    elif args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"generated markdown written to {args.output}")
    else:
        print(markdown)

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Handle the config command."""
    config = Config.default()

    # update from args
    if args.include:
        config.include = args.include
    if args.exclude:
        config.exclude = args.exclude

    if args.config_type == "pyproject.toml":
        print(config.to_example_toml("tool.meadoc"))
    elif args.config_type == "meadoc.toml":
        print(config.to_example_toml("meadoc"))
    else:
        # print general config documentation
        print("""meadow configuration

configuration is loaded from (in order of precedence):
  1. .meadoc.toml
  2. meadoc.toml
  3. pyproject.toml (use [tool.meadoc] section)

run 'meadoc config pyproject.toml' or 'meadoc config meadoc.toml' to see
example configuration for each file type.
""")

    return 0


def cmd_about(args: argparse.Namespace) -> int:
    """Handle the about command."""
    print("""the meadow Docstring Format

a plaintext-first alternative documentation string style for Python

key features:
  - easy and intuitive to read and write
  - closely follows Python syntax, including type annotations
  - works best on Zed, okay on Visual Studio Code, eh on PyCharm

section types (in order):
  1. preamble (required) - one-line description
  2. body (optional) - longer explanation
  3. attributes/arguments/parameters - incoming signatures
  4. functions/methods - outgoing signatures
  5. returns - return type annotation
  6. raises - exception classes
  7. usage (optional) - code examples

example:
    \"\"\"a baker's confectionery, usually baked, a lie

    attributes:
        `name: str`
            name of the cake
        `ingredients: list[Ingredient]`
            ingredients of the cake

    methods:
        `def bake(self, override: BakingOverride | None = None) -> bool`
            bakes the cake and returns True if successful
    \"\"\"

see the full documentation at: https://github.com/markjoshwel/meadow
""")

    return 0


def main(args: list[str] | None = None) -> int:
    """Main entry point for meadoc."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    commands = {
        "format": cmd_format,
        "check": cmd_check,
        "generate": cmd_generate,
        "config": cmd_config,
        "about": cmd_about,
    }

    command_func = commands.get(parsed_args.command)
    if command_func:
        return command_func(parsed_args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
