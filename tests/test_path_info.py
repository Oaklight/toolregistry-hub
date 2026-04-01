"""Unit tests for PathInfo module."""

import os
import tempfile

from toolregistry_hub.path_info import PathInfo


class TestPathInfo:
    """Test cases for PathInfo.info()."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.test_subdir = os.path.join(self.temp_dir, "subdir")

        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("Hello, world!")  # 13 bytes

        os.makedirs(self.test_subdir, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment after each test."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_nonexistent_path(self):
        """Non-existent path returns {"exists": False} only."""
        result = PathInfo.info(os.path.join(self.temp_dir, "no_such_file"))
        assert result == {"exists": False}

    def test_file_info(self):
        """Regular file returns correct metadata."""
        result = PathInfo.info(self.test_file)
        assert result["exists"] is True
        assert result["type"] == "file"
        assert result["size"] == 13
        assert isinstance(result["last_modified"], str)
        assert "T" in result["last_modified"]  # ISO 8601
        assert isinstance(result["permissions"], str)
        assert len(result["permissions"]) == 9  # e.g. "rw-r--r--"

    def test_directory_info(self):
        """Directory returns correct metadata."""
        result = PathInfo.info(self.test_subdir)
        assert result["exists"] is True
        assert result["type"] == "directory"
        assert result["size"] == 0  # empty directory

    def test_directory_size_recursive(self):
        """Directory size is the sum of all contained file sizes."""
        # Create files inside subdirectory
        for name in ("a.txt", "b.txt"):
            with open(os.path.join(self.test_subdir, name), "w") as f:
                f.write("12345")  # 5 bytes each

        result = PathInfo.info(self.test_subdir)
        assert result["size"] == 10

    def test_symlink(self):
        """Symlink is reported as type 'symlink'."""
        link_path = os.path.join(self.temp_dir, "link.txt")
        os.symlink(self.test_file, link_path)
        result = PathInfo.info(link_path)
        assert result["exists"] is True
        assert result["type"] == "symlink"
        assert result["size"] == 13

    def test_permissions_format(self):
        """Permissions string is 9 characters like 'rwxr-xr-x'."""
        result = PathInfo.info(self.test_file)
        perms = result["permissions"]
        assert len(perms) == 9
        for ch in perms:
            assert ch in "rwxsStT-"

    def test_last_modified_iso8601(self):
        """last_modified is a valid ISO 8601 string ending with UTC offset."""
        from datetime import datetime

        result = PathInfo.info(self.test_file)
        ts = result["last_modified"]
        # Should be parseable as ISO 8601
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo is not None  # has timezone info

    def test_return_keys_for_existing_path(self):
        """Existing path returns exactly the expected keys."""
        result = PathInfo.info(self.test_file)
        assert set(result.keys()) == {
            "exists",
            "type",
            "size",
            "last_modified",
            "permissions",
        }
