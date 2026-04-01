"""File system operations module providing file and directory utilities.

This module contains the FileSystem class and convenience functions for:
- File and directory existence checks
- File reading/writing
- Directory listing
- File/directory copy/move/delete
- Path manipulation

Example:
    ```python
    from toolregistry_hub import FileSystem
    fs = FileSystem()
    fs.create_dir('new_dir')
    # Note: create_file is part of FileSystem, write_file is in FileOps
    fs.create_file('new_dir/file.txt', 'content')
    fs.list_dir('new_dir')  # ['file.txt']
    ```
"""

import os
import shutil
import stat  # Import stat for file attributes
import warnings
from pathlib import Path

_DEPRECATION_MSG = (
    "FileSystem is deprecated and will be removed in a future release. "
    "Use PathInfo.info() for metadata queries, FileSearch for file discovery, "
    "and FileOps for file manipulation."
)


class FileSystem:
    """Provides file system operations related to structure, state, and metadata.

    .. deprecated::
        This class is deprecated. Use the following replacements:

        - ``exists``, ``is_file``, ``is_dir``, ``get_size``,
          ``get_last_modified_time`` → :meth:`PathInfo.info`
        - ``list_dir`` → :meth:`FileSearch.tree` / :meth:`FileSearch.glob`
        - ``copy``, ``move``, ``delete`` → ``BashTool`` (pending)
        - ``create_file``, ``create_dir`` → :meth:`FileOps.write_file`
          / ``BashTool``
        - ``join_paths``, ``get_absolute_path`` → model can concatenate
          paths directly
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)

    @staticmethod
    def exists(path: str) -> bool:
        """Checks if a path exists.

        .. deprecated:: Use ``PathInfo.info(path)["exists"]`` instead.

        Args:
            path: The path string to check.

        Returns:
            True if path exists, False otherwise
        """
        warnings.warn(
            "FileSystem.exists() is deprecated. Use PathInfo.info(path) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Path(path).exists()

    @staticmethod
    def is_file(path: str) -> bool:
        """Checks if a path points to a file.

        .. deprecated:: Use ``PathInfo.info(path)["type"] == "file"`` instead.

        Args:
            path: The path string to check.

        Returns:
            True if the path points to a file, False otherwise.
        """
        warnings.warn(
            "FileSystem.is_file() is deprecated. Use PathInfo.info(path) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Path(path).is_file()

    @staticmethod
    def is_dir(path: str) -> bool:
        """Checks if a path points to a directory.

        .. deprecated:: Use ``PathInfo.info(path)["type"] == "directory"`` instead.

        Args:
            path: The path string to check.

        Returns:
            True if the path points to a directory, False otherwise.
        """
        warnings.warn(
            "FileSystem.is_dir() is deprecated. Use PathInfo.info(path) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Path(path).is_dir()

    @staticmethod
    def _is_hidden(path_obj: Path) -> bool:
        """Checks if a file/directory should be considered hidden based on OS conventions."""
        # Always check for '.' prefix first (common across OSes)
        if path_obj.name.startswith("."):
            return True
        # On Windows, also check the hidden attribute
        if os.name == "nt":
            try:
                attrs = path_obj.stat().st_file_attributes
                if attrs & stat.FILE_ATTRIBUTE_HIDDEN:
                    return True
            except OSError:  # Handle potential errors like permission denied
                return True  # Treat as hidden if attributes can't be read
        return False

    @staticmethod
    def list_dir(path: str, depth: int = 1, show_hidden: bool = False) -> list[str]:
        """Lists contents of a directory up to a specified depth.

        .. deprecated:: Use ``FileSearch.tree()`` or ``FileSearch.glob()`` instead.

        Args:
            path: The directory path string to list.
            depth: Maximum depth to list (default=1). Must be >= 1.
            show_hidden: If False, filters out hidden files/directories. On Unix-like systems (Linux, macOS),
                         this means names starting with '.'. On Windows, this means files/directories
                         with the 'hidden' attribute set, as well as names starting with '.'. (default is False).

        Returns:
            List of relative path strings of items in the directory up to the specified depth.

        Raises:
            ValueError: If depth is less than 1.
            FileNotFoundError: If the path does not exist or is not a directory.
        """
        warnings.warn(
            "FileSystem.list_dir() is deprecated. "
            "Use FileSearch.tree() or FileSearch.glob() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        base_path = Path(path)
        if not base_path.is_dir():
            raise FileNotFoundError(
                f"Path is not a directory or does not exist: {path}"
            )
        if depth < 1:
            raise ValueError("Depth must be 1 or greater.")

        if depth == 1:
            # For depth 1, return only the names of immediate children
            items = []
            for p in base_path.iterdir():
                if show_hidden or not FileSystem._is_hidden(p):
                    items.append(p.name)
            return items
        else:
            # For depth > 1, use rglob and filter by depth, returning relative paths
            results = []
            for p in base_path.rglob("*"):
                try:
                    relative_path = p.relative_to(base_path)
                    if len(relative_path.parts) <= depth:
                        # Determine if the item or its path makes it hidden
                        item_is_hidden = FileSystem._is_hidden(p)
                        path_contains_hidden = any(
                            part.startswith(".") for part in relative_path.parts
                        )

                        # Include if show_hidden is True, or if neither the item nor its path is hidden
                        if show_hidden or (
                            not item_is_hidden and not path_contains_hidden
                        ):
                            results.append(str(relative_path))

                except ValueError:
                    # This can happen under certain conditions, e.g., symlink loops, long paths
                    # Consider adding logging here if more detailed diagnostics are needed.
                    continue
                except PermissionError:
                    # Skip entries we don't have permission to access
                    continue
            return results

    @staticmethod
    def create_file(path: str) -> None:
        """Creates an empty file or updates the timestamp if it already exists (like 'touch').

        .. deprecated:: Use ``FileOps.write_file()`` instead.

        Args:
            path: The file path string to create or update.
        """
        warnings.warn(
            "FileSystem.create_file() is deprecated. Use FileOps.write_file() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        Path(path).touch()

    @staticmethod
    def copy(src: str, dst: str) -> None:
        """Copies a file or directory.

        .. deprecated:: Will be replaced by ``BashTool`` in a future release.

        Args:
            src: Source path string.
            dst: Destination path string.
        """
        warnings.warn(
            "FileSystem.copy() is deprecated. "
            "Will be replaced by BashTool in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        src_path = Path(src)
        dst_path = Path(dst)

        if src_path.is_file():
            shutil.copy2(src_path, dst_path)
        elif src_path.is_dir():  # Check if it's a directory before copying
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)  # Allow overwriting
        else:
            raise FileNotFoundError(f"Source path is not a file or directory: {src}")

    @staticmethod
    def move(src: str, dst: str) -> None:
        """Moves/renames a file or directory.

        .. deprecated:: Will be replaced by ``BashTool`` in a future release.

        Args:
            src: Source path string.
            dst: Destination path string.
        """
        warnings.warn(
            "FileSystem.move() is deprecated. "
            "Will be replaced by BashTool in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        src_path = Path(src)
        dst_path = Path(dst)
        # Use shutil.move for better cross-filesystem compatibility
        shutil.move(str(src_path), str(dst_path))  # shutil.move expects strings

    @staticmethod
    def delete(path: str) -> None:
        """Deletes a file or directory recursively.

        .. deprecated:: Will be replaced by ``BashTool`` in a future release.

        Args:
            path: Path string to delete.
        """
        warnings.warn(
            "FileSystem.delete() is deprecated. "
            "Will be replaced by BashTool in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        path_obj = Path(path)
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            shutil.rmtree(path_obj)
        # If it doesn't exist or is something else (like a broken symlink), do nothing or raise?
        # Current behavior: Fails silently if path doesn't exist or isn't file/dir after checks.

    @staticmethod
    def get_size(path: str) -> int:
        """Gets file/directory size in bytes (recursive for directories).

        .. deprecated:: Use ``PathInfo.info(path)["size"]`` instead.

        Args:
            path: Path string to check size of.

        Returns:
            Size in bytes.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        warnings.warn(
            "FileSystem.get_size() is deprecated. Use PathInfo.info(path) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if path_obj.is_file():
            return path_obj.stat().st_size
        elif path_obj.is_dir():
            return sum(f.stat().st_size for f in path_obj.rglob("*") if f.is_file())
        else:
            # Handle other path types like symlinks if necessary, or raise error
            return 0  # Or raise an error for unsupported types

    @staticmethod
    def get_last_modified_time(path: str) -> float:
        """Gets the last modified time of a file or directory.

        .. deprecated:: Use ``PathInfo.info(path)["last_modified"]`` instead.

        Args:
            path: Path string to the file or directory.

        Returns:
            Last modified time as a Unix timestamp (float).

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        warnings.warn(
            "FileSystem.get_last_modified_time() is deprecated. "
            "Use PathInfo.info(path) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        return path_obj.stat().st_mtime

    @staticmethod
    def join_paths(*paths: str) -> str:
        """Joins multiple path components into a normalized string path.

        .. deprecated:: LLMs can concatenate paths directly without a tool call.

        Args:
            *paths: One or more path component strings.

        Returns:
            Joined and normalized path string.
        """
        warnings.warn(
            "FileSystem.join_paths() is deprecated. "
            "LLMs can concatenate paths directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return str(Path(*paths))

    @staticmethod
    def get_absolute_path(path: str) -> str:
        """Gets the absolute path as a normalized string.

        .. deprecated:: LLMs can resolve paths directly without a tool call.

        Args:
            path: Path string to convert.

        Returns:
            Absolute path string.
        """
        warnings.warn(
            "FileSystem.get_absolute_path() is deprecated. "
            "LLMs can resolve paths directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return str(Path(path).absolute())

    @staticmethod
    def create_dir(path: str, parents: bool = True, exist_ok: bool = True) -> None:
        """Creates a directory, including parent directories if needed (defaults to True).

        .. deprecated:: Will be replaced by ``BashTool`` in a future release.

        Args:
            path: Directory path string to create.
            parents: Create parent directories if needed (default=True).
            exist_ok: Don't raise error if directory exists (default=True).
        """
        warnings.warn(
            "FileSystem.create_dir() is deprecated. "
            "Will be replaced by BashTool in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)
