"""tests for meadow discovery module
with all my heart, 2024-2025, mark joshwel <mark@joshwel.co>
SPDX-License-Identifier: Unlicense OR 0BSD
"""

from pathlib import Path

from meadow.config import Config
from meadow.discovery import (
    discover_python_files,
    get_relative_path,
    should_process_file,
)


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


class TestShouldProcessFile:
    """test suite for should_process_file"""

    def test_python_file_is_accepted(self, tmp_path: Path) -> None:
        """Test that python files are accepted"""
        py_file = tmp_path / "test.py"
        py_file.write_text("# test")

        config = Config.default()

        assert should_process_file(py_file, config) is True

    def test_non_python_file_is_rejected(self, tmp_path: Path) -> None:
        """Test that non-python files are rejected"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test")

        config = Config.default()

        assert should_process_file(txt_file, config) is False

    def test_excluded_file_is_rejected(self, tmp_path: Path) -> None:
        """Test that excluded files are rejected"""
        py_file = tmp_path / "__pycache__" / "test.py"
        py_file.parent.mkdir()
        py_file.write_text("# test")

        config = Config.default()

        assert should_process_file(py_file, config) is False


class TestGetRelativePath:
    """test suite for get_relative_path"""

    def test_relative_path(self) -> None:
        """Test getting relative path"""
        base = Path("/home/user/project")
        file = Path("/home/user/project/src/main.py")

        result = get_relative_path(file, base)

        # use as_posix() for cross-platform comparison
        assert result.replace("\\", "/") == "src/main.py"

    def test_absolute_path_when_not_relative(self) -> None:
        """Test that absolute path is returned when not relative"""
        base = Path("/home/user/project1")
        file = Path("/home/user/project2/main.py")

        result = get_relative_path(file, base)

        assert result == str(file)
