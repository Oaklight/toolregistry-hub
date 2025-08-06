"""Unit tests for FileSystem module."""

import os
import tempfile
import time

import pytest

from toolregistry_hub.filesystem import FileSystem


class TestFileSystem:
    """Test cases for FileSystem class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.test_dir = os.path.join(self.temp_dir, "test_subdir")

        # Create a test file
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("Test content")

        # Create a test directory
        os.makedirs(self.test_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment after each test."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_exists_file(self):
        """Test checking if file exists."""
        assert FileSystem.exists(self.test_file) is True
        assert (
            FileSystem.exists(os.path.join(self.temp_dir, "nonexistent.txt")) is False
        )

    def test_exists_directory(self):
        """Test checking if directory exists."""
        assert FileSystem.exists(self.test_dir) is True
        assert (
            FileSystem.exists(os.path.join(self.temp_dir, "nonexistent_dir")) is False
        )

    def test_is_file(self):
        """Test checking if path is a file."""
        assert FileSystem.is_file(self.test_file) is True
        assert FileSystem.is_file(self.test_dir) is False
        assert (
            FileSystem.is_file(os.path.join(self.temp_dir, "nonexistent.txt")) is False
        )

    def test_is_dir(self):
        """Test checking if path is a directory."""
        assert FileSystem.is_dir(self.test_dir) is True
        assert FileSystem.is_dir(self.test_file) is False
        assert (
            FileSystem.is_dir(os.path.join(self.temp_dir, "nonexistent_dir")) is False
        )

    def test_create_file(self):
        """Test creating a file (touch functionality)."""
        new_file = os.path.join(self.temp_dir, "new_file.txt")

        # File should not exist initially
        assert not FileSystem.exists(new_file)

        # Create the file
        FileSystem.create_file(new_file)

        # File should now exist and be a file
        assert FileSystem.exists(new_file)
        assert FileSystem.is_file(new_file)

    def test_create_file_update_timestamp(self):
        """Test updating timestamp of existing file."""
        original_mtime = FileSystem.get_last_modified_time(self.test_file)

        # Wait a bit to ensure timestamp difference
        time.sleep(0.1)

        # Touch the file
        FileSystem.create_file(self.test_file)

        new_mtime = FileSystem.get_last_modified_time(self.test_file)
        assert new_mtime > original_mtime

    def test_create_dir(self):
        """Test creating a directory."""
        new_dir = os.path.join(self.temp_dir, "new_directory")

        # Directory should not exist initially
        assert not FileSystem.exists(new_dir)

        # Create the directory
        FileSystem.create_dir(new_dir)

        # Directory should now exist
        assert FileSystem.exists(new_dir)
        assert FileSystem.is_dir(new_dir)

    def test_create_dir_with_parents(self):
        """Test creating nested directories."""
        nested_dir = os.path.join(self.temp_dir, "level1", "level2", "level3")

        # Create nested directory structure
        FileSystem.create_dir(nested_dir, parents=True)

        # All levels should exist
        assert FileSystem.exists(nested_dir)
        assert FileSystem.is_dir(nested_dir)

    def test_create_dir_exists_ok(self):
        """Test creating directory that already exists."""
        # Should not raise error when exist_ok=True (default)
        FileSystem.create_dir(self.test_dir)
        assert FileSystem.exists(self.test_dir)

    def test_list_dir_depth_1(self):
        """Test listing directory contents with depth 1."""
        # Create some test files and directories
        file1 = os.path.join(self.temp_dir, "file1.txt")
        file2 = os.path.join(self.temp_dir, "file2.py")
        subdir = os.path.join(self.temp_dir, "subdir")

        with open(file1, "w") as f:
            f.write("content1")
        with open(file2, "w") as f:
            f.write("content2")
        os.makedirs(subdir)

        contents = FileSystem.list_dir(self.temp_dir, depth=1)

        # Should contain all immediate children
        assert "file1.txt" in contents
        assert "file2.py" in contents
        assert "subdir" in contents
        assert "test.txt" in contents  # from setup
        assert "test_subdir" in contents  # from setup

    def test_list_dir_depth_2(self):
        """Test listing directory contents with depth 2."""
        # Create nested structure
        subdir = os.path.join(self.temp_dir, "subdir")
        nested_file = os.path.join(subdir, "nested.txt")

        os.makedirs(subdir)
        with open(nested_file, "w") as f:
            f.write("nested content")

        contents = FileSystem.list_dir(self.temp_dir, depth=2)

        # Should contain nested items
        assert "subdir/nested.txt" in contents or "subdir\\nested.txt" in contents

    def test_list_dir_hidden_files(self):
        """Test listing directory with hidden files."""
        # Create hidden file
        hidden_file = os.path.join(self.temp_dir, ".hidden")
        with open(hidden_file, "w") as f:
            f.write("hidden content")

        # Without show_hidden
        contents_no_hidden = FileSystem.list_dir(self.temp_dir, show_hidden=False)
        assert ".hidden" not in contents_no_hidden

        # With show_hidden
        contents_with_hidden = FileSystem.list_dir(self.temp_dir, show_hidden=True)
        assert ".hidden" in contents_with_hidden

    def test_list_dir_invalid_path(self):
        """Test listing non-existent directory."""
        with pytest.raises(FileNotFoundError):
            FileSystem.list_dir(os.path.join(self.temp_dir, "nonexistent"))

    def test_list_dir_invalid_depth(self):
        """Test listing with invalid depth."""
        with pytest.raises(ValueError, match="Depth must be 1 or greater"):
            FileSystem.list_dir(self.temp_dir, depth=0)

    def test_copy_file(self):
        """Test copying a file."""
        dest_file = os.path.join(self.temp_dir, "copied_file.txt")

        FileSystem.copy(self.test_file, dest_file)

        # Both files should exist
        assert FileSystem.exists(self.test_file)
        assert FileSystem.exists(dest_file)
        assert FileSystem.is_file(dest_file)

        # Content should be the same
        with open(self.test_file, "r") as f1, open(dest_file, "r") as f2:
            assert f1.read() == f2.read()

    def test_copy_directory(self):
        """Test copying a directory."""
        # Create content in source directory
        source_file = os.path.join(self.test_dir, "source_file.txt")
        with open(source_file, "w") as f:
            f.write("source content")

        dest_dir = os.path.join(self.temp_dir, "copied_dir")

        FileSystem.copy(self.test_dir, dest_dir)

        # Both directories should exist
        assert FileSystem.exists(self.test_dir)
        assert FileSystem.exists(dest_dir)
        assert FileSystem.is_dir(dest_dir)

        # Copied file should exist
        copied_file = os.path.join(dest_dir, "source_file.txt")
        assert FileSystem.exists(copied_file)

    def test_copy_nonexistent_source(self):
        """Test copying non-existent source."""
        nonexistent = os.path.join(self.temp_dir, "nonexistent")
        dest = os.path.join(self.temp_dir, "dest")

        with pytest.raises(FileNotFoundError):
            FileSystem.copy(nonexistent, dest)

    def test_move_file(self):
        """Test moving a file."""
        dest_file = os.path.join(self.temp_dir, "moved_file.txt")
        original_content = "Test content"

        FileSystem.move(self.test_file, dest_file)

        # Original should not exist, destination should exist
        assert not FileSystem.exists(self.test_file)
        assert FileSystem.exists(dest_file)
        assert FileSystem.is_file(dest_file)

        # Content should be preserved
        with open(dest_file, "r") as f:
            assert f.read() == original_content

    def test_move_directory(self):
        """Test moving a directory."""
        dest_dir = os.path.join(self.temp_dir, "moved_dir")

        FileSystem.move(self.test_dir, dest_dir)

        # Original should not exist, destination should exist
        assert not FileSystem.exists(self.test_dir)
        assert FileSystem.exists(dest_dir)
        assert FileSystem.is_dir(dest_dir)

    def test_delete_file(self):
        """Test deleting a file."""
        assert FileSystem.exists(self.test_file)

        FileSystem.delete(self.test_file)

        assert not FileSystem.exists(self.test_file)

    def test_delete_directory(self):
        """Test deleting a directory."""
        # Add content to directory
        test_file_in_dir = os.path.join(self.test_dir, "file_in_dir.txt")
        with open(test_file_in_dir, "w") as f:
            f.write("content")

        assert FileSystem.exists(self.test_dir)
        assert FileSystem.exists(test_file_in_dir)

        FileSystem.delete(self.test_dir)

        assert not FileSystem.exists(self.test_dir)
        assert not FileSystem.exists(test_file_in_dir)

    def test_get_size_file(self):
        """Test getting file size."""
        size = FileSystem.get_size(self.test_file)
        assert isinstance(size, int)
        assert size > 0  # Should have some content

    def test_get_size_directory(self):
        """Test getting directory size."""
        # Add more content to directory
        file_in_dir = os.path.join(self.test_dir, "file.txt")
        with open(file_in_dir, "w") as f:
            f.write("content in directory")

        size = FileSystem.get_size(self.test_dir)
        assert isinstance(size, int)
        assert size > 0

    def test_get_size_nonexistent(self):
        """Test getting size of non-existent path."""
        with pytest.raises(FileNotFoundError):
            FileSystem.get_size(os.path.join(self.temp_dir, "nonexistent"))

    def test_get_last_modified_time(self):
        """Test getting last modified time."""
        mtime = FileSystem.get_last_modified_time(self.test_file)
        assert isinstance(mtime, float)
        assert mtime > 0

    def test_get_last_modified_time_nonexistent(self):
        """Test getting last modified time of non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileSystem.get_last_modified_time(
                os.path.join(self.temp_dir, "nonexistent")
            )

    def test_join_paths(self):
        """Test joining path components."""
        joined = FileSystem.join_paths("path", "to", "file.txt")
        expected = os.path.join("path", "to", "file.txt")
        assert joined == expected

    def test_join_paths_single(self):
        """Test joining single path component."""
        joined = FileSystem.join_paths("single_path")
        assert joined == "single_path"

    def test_get_absolute_path(self):
        """Test getting absolute path."""
        abs_path = FileSystem.get_absolute_path(self.test_file)
        assert os.path.isabs(abs_path)
        assert abs_path.endswith("test.txt")

    def test_get_absolute_path_relative(self):
        """Test getting absolute path from relative path."""
        abs_path = FileSystem.get_absolute_path("relative/path")
        assert os.path.isabs(abs_path)
        assert "relative" in abs_path
        assert "path" in abs_path
