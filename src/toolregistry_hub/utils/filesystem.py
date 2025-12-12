"""
filesystem utilities for file operations.
"""

import os
import pathlib
from typing import Dict, Union


def validate_path(path: str) -> Dict[str, Union[bool, str]]:
    """Validate file path safety in an OS-agnostic way (3.8+)."""
    if not path:
        return {"valid": False, "message": "Empty path"}

    # Normalize path separators and expand user
    path = os.path.expanduser(path)
    path = os.path.normpath(path)

    # Reject any path containing glob or shell metacharacters
    # pathlib.PurePath.parts works the same on every OS
    dangerous = {"*", "?", '"', "'", "<", ">", "|"}
    for part in pathlib.PurePath(path).parts:
        if any(c in part for c in dangerous):
            return {"valid": False, "message": "Contains dangerous characters"}

    return {"valid": True, "message": ""}
