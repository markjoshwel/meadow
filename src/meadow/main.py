"""meadow: a docstring machine based on typing information.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

main entry point for the meadoc command-line interface.
"""


import argparse
import json
import sys
from pathlib import Path
from typing import Literal, TypedDict, cast


class FileResult(TypedDict):
    """result type for file processing in format command

    attributes:
        `file: str`
            path to the file
        `generated: int`
            number of docstrings generated
        `updated: int`
            number of docstrings updated
        `skipped: int`
            number of docstrings skipped
        `malformed: int`
            number of malformed docstrings
    """

    file: str
    generated: int
    updated: int
    skipped: int
    malformed: int


class Issue(TypedDict):
    """issue type for check command

    attributes:
        `file: str`
            path to the file
        `line: int`
            line number
        `column: int`
            column number
        `code: str`
            error code
        `message: str`
            error message
        `severity: str`
            severity level
    """

    file: str
    line: int
    column: int
    code: str
    message: str
    severity: str


from ._version import __version__
from .config import Config, find_project_root
from .discovery import discover_python_files
from .errors import ErrorSeverity
from .generator import DocstringUpdater
from .markdown import MarkdownGenerator
from .validator import MDFValidator


def create_parser() -> argparse.ArgumentParser:
    """create the argument parser for meadoc.

    returns: `argparse.ArgumentParser`
        configured argument parser with all subcommands
    """
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
        choices=["pyproject.toml", "meadoc.toml", ".meadoc.toml"],
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
    """add common arguments to format, check, and generate subparsers.

    arguments:
        `parser: argparse.ArgumentParser`
            the argument parser to add arguments to

    returns: `none`
        no return value
    """
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
    """add config-specific arguments to the config subparser.

    arguments:
        `parser: argparse.ArgumentParser`
            the argument parser to add arguments to

    returns: `none`
        no return value
    """
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
    """handle the format command to generate or update docstrings.

    arguments:
        `args: argparse.Namespace`
            parsed command-line arguments

    returns: `int`
        exit code (0 for success)
    """
    config = Config.load()

    # update config from args
    include_patterns = cast(list[str] | None, args.include)
    exclude_patterns = cast(list[str] | None, args.exclude)
    sources = cast(list[Path], args.source)
    respect_gitignore_flag = not cast(bool, args.disrespect_gitignore)
    plumbing_mode = cast(bool, args.plumbing)
    fix_malformed_flag = cast(bool, args.fix_malformed)

    if include_patterns:
        config.include = include_patterns
    if exclude_patterns:
        config.exclude.extend(exclude_patterns)

    # discover files
    files = list(
        discover_python_files(
            sources,
            config,
            respect_gitignore=respect_gitignore_flag,
        )
    )

    if not files:
        if plumbing_mode:
            print(json.dumps({"files": [], "summary": "no files found"}))
        else:
            print("no files found")
        return 0

    # process files
    updater = DocstringUpdater(config)
    results: list[FileResult] = []

    for file_path in files:
        update_result = updater.update_file(
            file_path, fix_malformed=fix_malformed_flag
        )
        file_result: FileResult = {
            "file": str(file_path),
            "generated": update_result["generated"],
            "updated": update_result["updated"],
            "skipped": update_result["skipped"],
            "malformed": update_result["malformed"],
        }
        results.append(file_result)

    # output results
    if plumbing_mode:
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

        # print summary
        total_generated = sum(r["generated"] for r in results)
        total_updated = sum(r["updated"] for r in results)
        total_skipped = sum(r["skipped"] for r in results)
        total_malformed = sum(r["malformed"] for r in results)

        summary_parts: list[str] = []
        if total_generated:
            summary_parts.append(f"{total_generated} generated")
        if total_updated:
            summary_parts.append(f"{total_updated} updated")
        if total_skipped:
            summary_parts.append(f"{total_skipped} skipped")
        if total_malformed:
            summary_parts.append(f"{total_malformed} malformed")

        if summary_parts:
            print(f"{', '.join(summary_parts)}")
        else:
            print("no changes needed")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """handle the check command to validate docstrings.

    arguments:
        `args: argparse.Namespace`
            parsed command-line arguments

    returns: `int`
        exit code (0 if no errors, 1 if issues found)
    """
    config = Config.load()

    # update config from args
    include_patterns = cast(list[str] | None, args.include)
    exclude_patterns = cast(list[str] | None, args.exclude)
    sources = cast(list[Path], args.source)
    respect_gitignore_flag = not cast(bool, args.disrespect_gitignore)
    plumbing_mode = cast(bool, args.plumbing)

    if include_patterns:
        config.include = include_patterns
    if exclude_patterns:
        config.exclude.extend(exclude_patterns)

    # discover files
    files = list(
        discover_python_files(
            sources,
            config,
            respect_gitignore=respect_gitignore_flag,
        )
    )

    if not files:
        if plumbing_mode:
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
    all_issues: list[Issue] = []
    has_errors = False

    for file_path in files:
        diagnostics = validator.validate_file(file_path)

        for diag in diagnostics:
            issue: Issue = {
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
    if plumbing_mode:
        print(
            json.dumps(
                {"files": [str(f) for f in files], "issues": all_issues}
            )
        )
    else:
        for issue in all_issues:
            print(
                f"{issue['file']}:{issue['line']}:{issue['column']}: {issue['code']}: {issue['message']}"
            )

        # print summary
        error_count = sum(1 for i in all_issues if i["severity"] == "ERROR")
        warning_count = sum(
            1 for i in all_issues if i["severity"] == "WARNING"
        )
        info_count = sum(1 for i in all_issues if i["severity"] == "INFO")

        if error_count or warning_count or info_count:
            parts: list[str] = []
            if error_count:
                parts.append(f"{error_count} error(s)")
            if warning_count:
                parts.append(f"{warning_count} warning(s)")
            if info_count:
                parts.append(f"{info_count} info")
            print(f"{', '.join(parts)}")
        else:
            print("success - no issues found")

    return 1 if has_errors else 0


def cmd_generate(args: argparse.Namespace) -> int:
    """handle the generate command to create markdown api documentation.

    arguments:
        `args: argparse.Namespace`
            parsed command-line arguments

    returns: `int`
        exit code (0 for success)
    """
    config = Config.load()

    # update config from args
    include_patterns = cast(list[str] | None, args.include)
    exclude_patterns = cast(list[str] | None, args.exclude)
    sources = cast(list[Path], args.source)
    respect_gitignore_flag = not cast(bool, args.disrespect_gitignore)
    plumbing_mode = cast(bool, args.plumbing)
    output_path_str = cast(str | None, args.output)
    starting_header = cast(Literal[1, 2, 3, 4, 5, 6], args.starting_header)
    no_toc = cast(bool, args.no_toc)

    if include_patterns:
        config.include = include_patterns
    if exclude_patterns:
        config.exclude.extend(exclude_patterns)

    # update generate config from CLI args
    config.generate.starting_header_level = starting_header
    if no_toc:
        config.generate.include_toc = False

    # discover files
    files = list(
        discover_python_files(
            sources,
            config,
            respect_gitignore=respect_gitignore_flag,
        )
    )

    if not files:
        if plumbing_mode:
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

    # collect and update external links
    external_types = generator.collect_external_types(files)
    if external_types:
        generator.update_external_links(external_types, base_path)

    # output results
    if plumbing_mode:
        print(
            json.dumps(
                {"files": [str(f) for f in files], "markdown": markdown}
            )
        )
    elif output_path_str:
        output_path = Path(output_path_str)
        _ = output_path.write_text(markdown, encoding="utf-8")
        print(f"generated markdown written to {output_path_str}")
        print(f"\nprocessed {len(files)} file(s)")
    else:
        print(markdown)
        print(f"\nprocessed {len(files)} file(s)")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """handle the config command to display configuration documentation.

    arguments:
        `args: argparse.Namespace`
            parsed command-line arguments

    returns: `int`
        exit code (0 for success)
    """
    config = Config.default()

    # update from args
    include_patterns = cast(list[str] | None, args.include)
    exclude_patterns = cast(list[str] | None, args.exclude)
    config_type = cast(str | None, args.config_type)

    if include_patterns:
        config.include = include_patterns
    if exclude_patterns:
        config.exclude = exclude_patterns

    if config_type == "pyproject.toml":
        print(config.to_example_toml("tool.meadoc"))
    elif config_type in ("meadoc.toml", ".meadoc.toml"):
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


def cmd_about(_args: argparse.Namespace) -> int:
    """handle the about command to display format documentation.

    reads and displays the README.md from the bundled package or repository.

    arguments:
        `_args: argparse.Namespace`
            parsed command-line arguments (unused)

    returns: `int`
        exit code (0 for success)
    """
    # try to find README.md in various locations
    readme_paths = [
        # bundled with package (wheel)
        Path(__file__).parent / "README.md",
        # development mode (repo root)
        Path(__file__).parent.parent.parent / "README.md",
        # current working directory
        Path.cwd() / "README.md",
    ]

    readme_content: str | None = None
    for readme_path in readme_paths:
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding="utf-8")
                break
            except (OSError, UnicodeDecodeError):
                continue

    if readme_content:
        print(readme_content)
    else:
        # fallback: print basic info
        print("""the meadow Docstring Format

a plaintext-first alternative documentation string style for Python

see the full documentation at: https://github.com/markjoshwel/meadow
""")

    return 0


def main(args: list[str] | None = None) -> int:
    """main entry point for the meadoc cli.

    arguments:
        `args: list[str] | None = None`
            command-line arguments (defaults to sys.argv if None)

    returns: `int`
        exit code (0 for success)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    command = cast(str | None, parsed_args.command)
    if not command:
        parser.print_help()
        return 0

    commands = {
        "format": cmd_format,
        "check": cmd_check,
        "generate": cmd_generate,
        "config": cmd_config,
        "about": cmd_about,
    }

    command_func = commands.get(command)
    if command_func:
        return command_func(parsed_args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
