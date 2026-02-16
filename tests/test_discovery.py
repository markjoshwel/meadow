"""tests for meadow discovery module
with all my heart, 2024-2025, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""

from pathlib import Path

from meadoc.config import Config
from meadoc.discovery import discover_python_files


class TestDiscoverPythonFiles:
    """test suite for file discovery"""

    def test_discover_single_file(self, tmp_path: Path) -> None:
        """Test discovering a single file"""
        py_file = tmp_path / "test.py"
        py_file.write_text("# test")

        config = Config.default()
        files = list(discover_python_files([py_file], config))

        assert len(files) == 1
        assert files[0] == py_file.resolve()

    def test_discover_from_directory(self, tmp_path: Path) -> None:
        """Test discovering files in a directory"""
        # create some python files
        (tmp_path / "a.py").write_text("# a")
        (tmp_path / "b.py").write_text("# b")

        # create a subdirectory with more files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "c.py").write_text("# c")

        config = Config.default()
        config.include = ["**/*.py"]
        config.exclude = []

        files = list(discover_python_files([tmp_path], config))

        assert len(files) == 3

    def test_respect_exclude_patterns(self, tmp_path: Path) -> None:
        """Test that exclude patterns are respected"""
        (tmp_path / "include.py").write_text("# include")
        (tmp_path / "exclude.py").write_text("# exclude")

        config = Config.default()
        config.include = ["**/*.py"]
        config.exclude = ["exclude.py"]

        files = list(discover_python_files([tmp_path], config))

        assert len(files) == 1
        assert "include.py" in str(files[0])

    def test_ignore_non_python_files(self, tmp_path: Path) -> None:
        """Test that non-python files are ignored"""
        (tmp_path / "script.py").write_text("# python")
        (tmp_path / "readme.md").write_text("# markdown")
        (tmp_path / "data.txt").write_text("text")

        config = Config.default()
        config.include = ["**/*.py"]
        config.exclude = []

        files = list(discover_python_files([tmp_path], config))

        assert len(files) == 1
        assert files[0].name == "script.py"
