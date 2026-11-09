"""Unified file/directory metadata query.

Provides a single-call interface to retrieve path metadata (existence, type,
size, modification time, permissions).
"""

import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from toolregistry import ToolTag

from ._metadata import tool_metadata


class PathInfoResult(TypedDict, total=False):
    """Result of ``PathInfo.info``."""

    exists: bool
    type: str
    size: int
    last_modified: str
    permissions: str


class PathInfo:
    """File and directory metadata query."""

    @staticmethod
    @tool_metadata(
        defer=True,
        tags={ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=False,
        title="Path Info",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "exists": {"type": "boolean"},
                    "type": {"type": "string"},
                    "size": {"type": "integer"},
                    "last_modified": {"type": "string"},
                    "permissions": {"type": "string"},
                },
                "additionalProperties": True,
            }
        },
    )
    def info(path: str) -> PathInfoResult:
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
            return PathInfoResult(exists=False)

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

        return PathInfoResult(
            exists=True,
            type=path_type,
            size=size,
            last_modified=last_modified,
            permissions=permissions,
        )
