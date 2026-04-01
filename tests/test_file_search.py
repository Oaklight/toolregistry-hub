"""Unit tests for FileSearch module."""

import os
import shutil
import tempfile

import pytest

from toolregistry_hub.file_search import FileSearch


class TestFileSearchGlob:
    """Test cases for FileSearch.glob()."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create a small file tree:
        #   root/
        #     a.py
        #     b.txt
        #     sub/
        #       c.py
        #       d.txt
        #       deep/
        #         e.py
        self.sub = os.path.join(self.temp_dir, "sub")
        self.deep = os.path.join(self.sub, "deep")
        os.makedirs(self.deep)

        for name in ("a.py", "b.txt"):
            Path = os.path.join(self.temp_dir, name)
            with open(Path, "w") as f:
                f.write(name)

        for name in ("c.py", "d.txt"):
            with open(os.path.join(self.sub, name), "w") as f:
                f.write(name)

        with open(os.path.join(self.deep, "e.py"), "w") as f:
            f.write("e.py")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_recursive_glob(self):
        result = FileSearch.glob("**/*.py", root=self.temp_dir)
        names = sorted(os.path.basename(p) for p in result)
        assert names == ["a.py", "c.py", "e.py"]

    def test_non_recursive_glob(self):
        result = FileSearch.glob("*.py", root=self.temp_dir, recursive=False)
        names = [os.path.basename(p) for p in result]
        assert names == ["a.py"]

    def test_glob_no_match(self):
        result = FileSearch.glob("*.rs", root=self.temp_dir)
        assert result == []

    def test_glob_invalid_root(self):
        with pytest.raises(FileNotFoundError):
            FileSearch.glob("*", root=os.path.join(self.temp_dir, "nope"))

    def test_glob_returns_relative_paths(self):
        result = FileSearch.glob("**/*.py", root=self.temp_dir)
        for p in result:
            assert not os.path.isabs(p)


class TestFileSearchGrep:
    """Test cases for FileSearch.grep()."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_a = os.path.join(self.temp_dir, "a.py")
        self.file_b = os.path.join(self.temp_dir, "b.txt")

        with open(self.file_a, "w") as f:
            f.write("import os\nimport sys\nprint('hello')\n")

        with open(self.file_b, "w") as f:
            f.write("no matches here\njust text\n")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_grep_finds_matches(self):
        results = FileSearch.grep("import", path=self.temp_dir)
        assert len(results) == 2
        assert all(r["content"].startswith("import") for r in results)

    def test_grep_line_numbers(self):
        results = FileSearch.grep("print", path=self.temp_dir)
        assert len(results) == 1
        assert results[0]["line_number"] == 3

    def test_grep_single_file(self):
        results = FileSearch.grep("import", path=self.file_a)
        assert len(results) == 2

    def test_grep_file_pattern(self):
        results = FileSearch.grep(".", path=self.temp_dir, file_pattern="*.py")
        files = {r["file"] for r in results}
        assert all(f.endswith(".py") for f in files)

    def test_grep_no_match(self):
        results = FileSearch.grep("zzzzz_no_match", path=self.temp_dir)
        assert results == []

    def test_grep_max_results(self):
        results = FileSearch.grep(".", path=self.temp_dir, max_results=2)
        assert len(results) <= 2

    def test_grep_invalid_path(self):
        with pytest.raises(FileNotFoundError):
            FileSearch.grep("x", path=os.path.join(self.temp_dir, "nope"))

    def test_grep_invalid_regex(self):
        with pytest.raises(Exception):
            FileSearch.grep("[invalid", path=self.temp_dir)

    def test_grep_returns_relative_paths(self):
        results = FileSearch.grep("import", path=self.temp_dir)
        for r in results:
            assert not os.path.isabs(r["file"])


class TestFileSearchTree:
    """Test cases for FileSearch.tree()."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sub = os.path.join(self.temp_dir, "sub")
        self.deep = os.path.join(self.sub, "deep")
        os.makedirs(self.deep)

        with open(os.path.join(self.temp_dir, "file.txt"), "w") as f:
            f.write("x")
        with open(os.path.join(self.sub, "code.py"), "w") as f:
            f.write("x")
        with open(os.path.join(self.deep, "inner.py"), "w") as f:
            f.write("x")

        # Hidden file
        with open(os.path.join(self.temp_dir, ".hidden"), "w") as f:
            f.write("x")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_tree_basic(self):
        output = FileSearch.tree(self.temp_dir)
        assert "sub/" in output
        assert "file.txt" in output

    def test_tree_hidden_excluded_by_default(self):
        output = FileSearch.tree(self.temp_dir)
        assert ".hidden" not in output

    def test_tree_hidden_included(self):
        output = FileSearch.tree(self.temp_dir, show_hidden=True)
        assert ".hidden" in output

    def test_tree_max_depth(self):
        output = FileSearch.tree(self.temp_dir, max_depth=1)
        assert "sub/" in output
        # deep/ should not appear at depth 1
        assert "deep/" not in output

    def test_tree_file_pattern(self):
        output = FileSearch.tree(self.temp_dir, file_pattern="*.py")
        assert "code.py" in output
        assert "file.txt" not in output

    def test_tree_invalid_path(self):
        with pytest.raises(FileNotFoundError):
            FileSearch.tree(os.path.join(self.temp_dir, "nope"))

    def test_tree_invalid_depth(self):
        with pytest.raises(ValueError):
            FileSearch.tree(self.temp_dir, max_depth=0)

    def test_tree_uses_connectors(self):
        output = FileSearch.tree(self.temp_dir)
        assert "├" in output or "└" in output
