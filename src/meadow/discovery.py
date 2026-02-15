"""file discovery for meadow using libsightseeing.

with all my heart, 2026, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""

from collections.abc import Iterator
from pathlib import Path

from libsightseeing import SourceResolver

from .config import Config


def discover_python_files(
    sources: list[Path],
    config: Config,
    respect_gitignore: bool = True,
) -> Iterator[Path]:
    """discover python files

    arguments:
        `sources: list[Path]`
            source files or directories
        `config: Config`
            configuration
        `respect_gitignore: bool = True`
            respect gitignore files

    yields: `Path`
        paths to python files

    returns: `Iterator[Path]`
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

    yield from sorted(all_files)
