"""file discovery for meadow using libsightseeing.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module provides file discovery capabilities, using libsightseeing for
file finding with gitignore support and include/exclude pattern matching.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from libsightseeing import SourceResolver

from .config import Config


def discover_python_files(
    sources: list[Path],
    config: Config,
    respect_gitignore: bool = True,
) -> Iterator[Path]:
    """discover python files based on sources and configuration

    uses libsightseeing SourceResolver for efficient file discovery with
    gitignore support and pattern matching.

    arguments:
        `sources: list[Path]`
            list of source files or directories to search
        `config: Config`
            meadow configuration with include/exclude patterns
        `respect_gitignore: bool = True`
            whether to respect .gitignore files

    yields: `Path`
        paths to python files

    returns: `none`
        no return value
    """
    if not sources:
        # default to current directory
        sources = [Path.cwd()]

    # collect all files
    all_files: set[Path] = set()

    # use include patterns from config if available, otherwise default
    include_patterns = config.include if config.include else ["**/*.py"]
    exclude_patterns = config.exclude

    # respect gitignore from config unless overridden
    should_respect_gitignore = respect_gitignore and config.respect_gitignore

    for source in sources:
        if source.is_file():
            if source.suffix == ".py":
                all_files.add(source.resolve())
        elif source.is_dir():
            # Adjust include patterns to be relative to the source directory
            # e.g., if source is 'src' and pattern is 'src/**/*.py', use '**/*.py'
            source_name = source.name
            adjusted_patterns: list[str] = []
            for pattern in include_patterns:
                if pattern.startswith(f"{source_name}/"):
                    adjusted_patterns.append(pattern[len(source_name) + 1 :])
                else:
                    adjusted_patterns.append(pattern)

            # use libsightseeing for directory traversal
            resolver = SourceResolver(
                root=source,
                include=adjusted_patterns,
                exclude=exclude_patterns,
                respect_gitignore=should_respect_gitignore,
            )
            for file_path in resolver.resolve():
                all_files.add(file_path.resolve())

    # yield sorted files for consistent ordering
    for file_path in sorted(all_files):
        yield file_path


def should_process_file(
    file_path: Path,
    config: Config,
    _respect_gitignore: bool = True,
) -> bool:
    """check if a file should be processed based on configuration

    arguments:
        `file_path: Path`
            the file to check
        `config: Config`
            meadow configuration
        `_respect_gitignore: bool = True`
            whether to respect .gitignore files (unused, kept for api compatibility)

    returns: `bool`
        true if the file should be processed
    """
    # check if it's a python file
    if file_path.suffix != ".py":
        return False

    # check exclude patterns
    exclude_patterns = config.exclude
    name = file_path.name
    path_str = str(file_path)

    for pattern in exclude_patterns:
        # exact match on filename
        if name == pattern:
            return False
        # glob match on filename
        import fnmatch

        if fnmatch.fnmatch(name, pattern):
            return False
        # glob match on full path
        if fnmatch.fnmatch(path_str, pattern):
            return False
        # check if any parent directory matches (for directory patterns)
        for parent in file_path.parents:
            parent_name = parent.name
            if parent_name == pattern:
                return False
            if fnmatch.fnmatch(parent_name, pattern):
                return False

    return True


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """get a relative path from base_path to file_path

    arguments:
        `file_path: Path`
            the target file path
        `base_path: Path`
            the base directory

    returns: `str`
        relative path as string
    """
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)
