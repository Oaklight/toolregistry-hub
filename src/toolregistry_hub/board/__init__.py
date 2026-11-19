"""Persistent project kanban for ToolRegistry Hub.

The package ships three pieces:

- :class:`BoardStore` — the SQLite store shared by every surface,
- :class:`BoardTools` — the ``board`` MCP tool namespace,
- :class:`BoardAdminExtension` — the admin panel tab (imported lazily by the
  standalone ``toolregistry-hub admin`` command, not from this module, so the
  package import stays free of admin-only code).
"""

from .paths import ENV_VAR, resolve_db_path
from .store import (
    CLOSED_STATUSES,
    PRIORITIES,
    PRIORITY_ALIASES,
    STATUS_ALIASES,
    STATUSES,
    BoardConflict,
    BoardError,
    BoardNotFound,
    BoardStore,
    BoardValidation,
    derive_key,
    normalize_priority,
    normalize_status,
)
from .tools import BoardTools

__all__ = [
    "BoardConflict",
    "BoardError",
    "BoardNotFound",
    "BoardStore",
    "BoardTools",
    "BoardValidation",
    "CLOSED_STATUSES",
    "ENV_VAR",
    "PRIORITIES",
    "PRIORITY_ALIASES",
    "STATUSES",
    "STATUS_ALIASES",
    "derive_key",
    "normalize_priority",
    "normalize_status",
    "resolve_db_path",
]
