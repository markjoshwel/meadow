"""file discovery for meadow using libsightseeing.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD

this module is a thin wrapper around libsightseeing for file discovery.
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
    """discover python files based on sources and configuration.

    arguments:
        `sources: list[Path]`
            source files or directories to search
        `config: Config`
            configuration with include/exclude patterns
        `respect_gitignore: bool = True`
            whether to respect .gitignore files

    yields: `Path`
        paths to python files
    """
    if not sources:
        sources = [Path.cwd()]

    include = config.include or ["**/*.py"]
    respect = respect_gitignore and config.respect_gitignore
    all_files: set[Path] = set()

    for source in sources:
        if source.is_file() and source.suffix == ".py":
            all_files.add(source.resolve())
        elif source.is_dir():
            # adjust patterns to be relative to source directory
            adjusted = [
                p[len(source.name) + 1 :]
                if p.startswith(f"{source.name}/")
                else p
                for p in include
            ]
            resolver = SourceResolver(
                root=source,
                include=adjusted,
                exclude=config.exclude,
                respect_gitignore=respect,
            )
            all_files.update(resolver.resolve())

    for f in sorted(all_files):
        yield f


def should_process_file(file_path: Path, config: Config) -> bool:
    """check if a file should be processed.

    arguments:
        `file_path: Path`
            the file to check
        `config: Config`
            configuration with exclude patterns

    returns: `bool`
        true if file should be processed
    """
    if file_path.suffix != ".py":
        return False

    name = file_path.name
    path_str = str(file_path)

    for pattern in config.exclude:
        if name == pattern:
            return False
        import fnmatch

        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(
            path_str, pattern
        ):
            return False
        for parent in file_path.parents:
            if parent.name == pattern or fnmatch.fnmatch(parent.name, pattern):
                return False

    return True


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """get relative path from base_path to file_path."""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)
