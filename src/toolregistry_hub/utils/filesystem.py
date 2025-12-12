"""
filesystem utilities for file operations.
"""

import os
import pathlib
from typing import Dict, Union


def validate_path(
    path: str, require_file: bool = False, require_dir: bool = False
) -> Dict[str, Union[bool, str]]:
    """Validate file path safety and optionally check if it's a file or directory.

    Args:
        path: Path to validate.
        require_file: If True, ensure path exists and is a regular file.
        require_dir: If True, ensure path exists and is a directory.

    Returns:
        Dict with "valid" (bool) and "message" (str).
    """
    if not path:
        return {"valid": False, "message": "Empty path"}

    # Normalize path separators and expand user
    path = os.path.expanduser(path)
    path = os.path.normpath(path)

    # Reject any path containing glob or shell metacharacters
    dangerous = {"*", "?", '"', "'", "<", ">", "|"}
    for part in pathlib.PurePath(path).parts:
        if any(c in part for c in dangerous):
            return {"valid": False, "message": "Contains dangerous characters"}

    # Existence and type checks
    if require_file or require_dir:
        if not os.path.exists(path):
            return {"valid": False, "message": f"Path does not exist: {path}"}
        if require_file and not os.path.isfile(path):
            return {"valid": False, "message": f"Path is not a regular file: {path}"}
        if require_dir and not os.path.isdir(path):
            return {"valid": False, "message": f"Path is not a directory: {path}"}

    return {"valid": True, "message": ""}
