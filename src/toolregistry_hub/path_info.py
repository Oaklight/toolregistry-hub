"""Unified file/directory metadata query.

Provides a single-call interface to retrieve path metadata (existence, type,
size, modification time, permissions), replacing the five separate query
methods on the legacy FileSystem class.
"""

import stat
from datetime import datetime, timezone
from pathlib import Path


class PathInfo:
    """File and directory metadata query."""

    @staticmethod
    def info(path: str) -> dict:
        """Get metadata for a file or directory in a single call.

        Args:
            path: Absolute or relative path to query.

        Returns:
            A dict with keys:
                - exists (bool)
                - type ("file" | "directory" | "symlink" | "other")
                - size (int, bytes) — for directories, total size of contents
                - last_modified (str, ISO 8601 in UTC)
                - permissions (str, e.g. "rwxr-xr-x")

            If path does not exist, returns ``{"exists": False}``.
        """
        p = Path(path)

        if not p.exists():
            return {"exists": False}

        st = p.stat()

        # Determine type
        if p.is_symlink():
            path_type = "symlink"
        elif p.is_file():
            path_type = "file"
        elif p.is_dir():
            path_type = "directory"
        else:
            path_type = "other"

        # Calculate size — recursive for directories
        if p.is_dir():
            size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        else:
            size = st.st_size

        # ISO 8601 timestamp in UTC
        last_modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()

        # Human-readable permissions string (e.g. "rwxr-xr-x")
        permissions = stat.filemode(st.st_mode)[1:]  # strip leading type char

        return {
            "exists": True,
            "type": path_type,
            "size": size,
            "last_modified": last_modified,
            "permissions": permissions,
        }
