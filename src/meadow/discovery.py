"""file discovery for meadow.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module provides file discovery capabilities, respecting gitignore patterns
and supporting include/exclude glob patterns.
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterator
from pathlib import Path

from meadow.config import Config


def discover_python_files(
    sources: list[Path],
    config: Config,
    respect_gitignore: bool = True,
) -> Iterator[Path]:
    """Discover python files based on sources and configuration.

    Arguments:
        `sources: list[Path]`
            list of source files or directories to search
        `config: Config`
            meadow configuration
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

    for source in sources:
        if source.is_file():
            if source.suffix == ".py":
                all_files.add(source.resolve())
        elif source.is_dir():
            # walk directory
            for root, dirs, files in os.walk(source):
                root_path = Path(root)

                # filter directories based on exclude patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not _matches_exclude(root_path / d, config.exclude)
                ]

                # check gitignore
                if respect_gitignore and config.respect_gitignore:
                    gitignore_path = root_path / ".gitignore"
                    if gitignore_path.exists():
                        gitignore_patterns = _parse_gitignore(gitignore_path)
                        dirs[:] = [
                            d
                            for d in dirs
                            if not _matches_gitignore(d, gitignore_patterns)
                        ]

                for file in files:
                    if file.endswith(".py"):
                        file_path = root_path / file

                        # check exclude patterns
                        if _matches_exclude(file_path, config.exclude):
                            continue

                        # check gitignore
                        if respect_gitignore and config.respect_gitignore:
                            gitignore_path = root_path / ".gitignore"
                            if gitignore_path.exists():
                                gitignore_patterns = _parse_gitignore(
                                    gitignore_path
                                )
                                if _matches_gitignore(
                                    file, gitignore_patterns
                                ):
                                    continue

                        all_files.add(file_path.resolve())

    # yield sorted files for consistent ordering
    for file_path in sorted(all_files):
        yield file_path


def _matches_exclude(file_path: Path, exclude_patterns: list[str]) -> bool:
    """Check if a file matches any exclude pattern."""
    path_str = str(file_path)
    name = file_path.name

    for pattern in exclude_patterns:
        # exact match on filename
        if name == pattern:
            return True
        # glob match on filename
        if fnmatch.fnmatch(name, pattern):
            return True
        # glob match on full path
        if fnmatch.fnmatch(path_str, pattern):
            return True
        # check if any parent directory matches (for directory patterns)
        for parent in file_path.parents:
            parent_name = parent.name
            if parent_name == pattern:
                return True
            if fnmatch.fnmatch(parent_name, pattern):
                return True

    return False


def _parse_gitignore(gitignore_path: Path) -> list[str]:
    """Parse a .gitignore file and return patterns."""
    patterns: list[str] = []

    try:
        with open(gitignore_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # skip negation patterns for simplicity
                if line.startswith("!"):
                    continue
                patterns.append(line)
    except Exception:
        pass

    return patterns


def _matches_gitignore(name: str, patterns: list[str]) -> bool:
    """Check if a name matches any gitignore pattern."""
    for pattern in patterns:
        # handle directory patterns
        if pattern.endswith("/"):
            pattern = pattern[:-1]

        # simple exact match
        if name == pattern:
            return True

        # glob match
        if fnmatch.fnmatch(name, pattern):
            return True

    return False


def should_process_file(
    file_path: Path,
    config: Config,
    respect_gitignore: bool = True,
) -> bool:
    """Check if a file should be processed based on configuration.

    Arguments:
        `file_path: Path`
            the file to check
        `config: Config`
            meadow configuration
        `respect_gitignore: bool = True`
            whether to respect .gitignore files

    returns: `bool`
        true if the file should be processed
    """
    # check if it's a python file
    if file_path.suffix != ".py":
        return False

    # check exclude patterns
    if _matches_exclude(file_path, config.exclude):
        return False

    # check gitignore
    if respect_gitignore and config.respect_gitignore:
        gitignore_path = file_path.parent / ".gitignore"
        if gitignore_path.exists():
            patterns = _parse_gitignore(gitignore_path)
            if _matches_gitignore(file_path.name, patterns):
                return False

    return True


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Get a relative path from base_path to file_path.

    Arguments:
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
