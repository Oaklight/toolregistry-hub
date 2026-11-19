"""Admin panel extension for the project kanban.

The extension is a thin HTTP surface over one
:class:`~toolregistry_hub.board.store.BoardStore`.  It implements the core
admin extension contract v1 (``ADMIN_EXTENSION_API``): routes under
``/ext/board``, assets under ``assets/ext/board/``, and one operator auth
level inherited from the panel.

The store is injected rather than looked up in ``ctx.registry``: the panel
must keep working when the board tool is disabled or absent from the served
preset, and both processes must agree on the database path.

Example:
    >>> from toolregistry import ToolRegistry
    >>> registry = ToolRegistry()
    >>> info = registry.enable_admin(extensions=[BoardAdminExtension(db=path)])
"""

from __future__ import annotations

import functools
import json
import sqlite3
from pathlib import Path
from typing import Any

from .store import (
    SCHEMA_VERSION,
    STATUSES,
    BoardConflict,
    BoardNotFound,
    BoardStorageError,
    BoardStore,
    BoardValidation,
)

#: Fields an entry write may carry.  Timestamps are server-owned, so they are
#: rejected here rather than silently ignored.
WRITABLE_FIELDS = frozenset(
    {
        "project",
        "title",
        "content",
        "status",
        "priority",
        "due",
        "labels",
        "assignee",
        "links",
    }
)

#: Extension name: URL segment and asset directory key.
NAME = "board"

#: Contract version, kept as a literal so the module imports on a core that
#: predates the contract; the host rejects a mismatch at startup.
REQUIRES_API = 1

_ASSETS_DIR = Path(__file__).with_name("assets")

#: Status columns in board order, for the panel's column layout.
COLUMNS = STATUSES


def _error(status: int, error: str, message: str) -> tuple[dict[str, str], int]:
    """Build the panel's JSON error shape."""
    return {"error": error, "message": message}, status


def _guard(handler: Any) -> Any:
    """Map store exceptions onto HTTP responses.

    The wrapper forwards every argument unchanged: the host calls a handler
    as ``handler(request, **path_params)``, and ``functools.wraps`` keeps the
    original signature for introspection.
    """

    @functools.wraps(handler)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return handler(*args, **kwargs)
        except BoardConflict as exc:
            return _error(409, "Conflict", str(exc))
        except BoardNotFound as exc:
            return _error(404, "Not Found", str(exc))
        except BoardValidation as exc:
            return _error(400, "Bad Request", str(exc))
        except (BoardStorageError, sqlite3.Error) as exc:
            return _error(503, "Service Unavailable", str(exc))
        except ValueError as exc:
            return _error(400, "Bad Request", str(exc))

    return wrapped


def _json_body(request: Any) -> dict[str, Any]:
    """Parse a request body that must be a JSON object."""
    if not request.body:
        raise BoardValidation("Request body is required")
    try:
        data = request.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise BoardValidation(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise BoardValidation("Body must be a JSON object")
    return data


def _reject_unknown(body: dict[str, Any], allowed: frozenset[str]) -> None:
    """Reject request keys outside *allowed*.

    Timestamps live in the same namespace as writable fields, so a silent
    drop would hide an attempt to set one.  Both write handlers apply this
    rule, which keeps ``POST`` and ``PATCH`` symmetric.

    Args:
        body: The decoded JSON object.
        allowed: Field names the handler accepts.

    Raises:
        BoardValidation: If the body carries an unknown key.
    """
    unknown = set(body) - allowed
    if unknown:
        raise BoardValidation(
            f"unsupported fields: {', '.join(sorted(map(str, unknown)))}"
        )


def _text(value: Any) -> str:
    """Return a string field, treating ``null`` as empty."""
    return "" if value is None else str(value)


def _optional_text(value: Any) -> str | None:
    """Return an optional string field, treating ``null`` as absent."""
    return None if value is None else str(value)


def _flag(request: Any, name: str) -> bool:
    """Return a boolean query flag such as ``?force=1``."""
    values = getattr(request, "query_params", {}) or {}
    raw = (values.get(name) or [""])[0]
    return str(raw).lower() in {"1", "true", "yes", "on"}


def _query(request: Any, name: str) -> str:
    """Return one query parameter value, or an empty string."""
    values = getattr(request, "query_params", {}) or {}
    return (values.get(name) or [""])[0]


class BoardAdminExtension:
    """Kanban tab backed by a shared :class:`BoardStore`.

    Args:
        store: An existing store, or ``None`` to build one from *db*.
        db: Database path used when *store* is ``None``.
        expose_path: Report the resolved database path in ``GET /meta``.
            The CLI disables it when the panel is not loopback-bound.
    """

    name = NAME
    title = {"en": "Kanban", "zh": "看板"}
    requires_api = REQUIRES_API
    entry = f"assets/ext/{NAME}/main.js"
    styles = (f"assets/ext/{NAME}/board.css",)
    assets = _ASSETS_DIR
    nav = {"group": "manage", "order": 30}
    icon = (
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
        "<rect x='3' y='4' width='5' height='16' rx='1'/>"
        "<rect x='10' y='4' width='5' height='10' rx='1'/>"
        "<rect x='17' y='4' width='4' height='13' rx='1'/></svg>"
    )

    def __init__(
        self,
        store: BoardStore | None = None,
        *,
        db: str | Path | None = None,
        expose_path: bool = True,
    ) -> None:
        self._store = store if store is not None else BoardStore(db)
        self._expose_path = expose_path

    @property
    def store(self) -> BoardStore:
        """The store the handlers use."""
        return self._store

    def register(self, ctx: Any) -> None:
        """Register the extension routes on *ctx*.

        Args:
            ctx: The host's ``AdminContext`` for this extension.
        """
        ctx.get("/projects", self.list_projects)
        ctx.post("/projects", self.create_project)
        ctx.patch("/projects/<key>", self.update_project)
        ctx.delete("/projects/<key>", self.remove_project)
        ctx.get("/board", self.board)
        ctx.get("/entries", self.list_entries)
        ctx.post("/entries", self.create_entry)
        ctx.get("/entries/<ref>", self.get_entry)
        ctx.patch("/entries/<ref>", self.update_entry)
        ctx.delete("/entries/<ref>", self.delete_entry)
        ctx.get("/meta", self.meta)

    # ---- meta ------------------------------------------------------------

    @_guard
    def meta(self, request: Any) -> dict[str, Any]:
        """Return the panel's schema and, on loopback, the database path."""
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "columns": list(COLUMNS),
        }
        if self._expose_path:
            payload["db_path"] = str(self._store.path)
        return payload

    # ---- projects --------------------------------------------------------

    @_guard
    def list_projects(self, request: Any) -> dict[str, Any]:
        """List projects with per-column counts."""
        include_archived = _flag(request, "include_archived")
        return {
            "projects": self._store.list_projects(include_archived=include_archived)
        }

    @_guard
    def create_project(self, request: Any) -> tuple[dict[str, Any], int]:
        """Create a project from ``{"name", "key"?}``."""
        body = _json_body(request)
        project = self._store.create_project(
            str(body.get("name", "")), str(body.get("key", "") or "")
        )
        return {"project": project}, 201

    @_guard
    def update_project(self, request: Any, key: str) -> dict[str, Any]:
        """Rename a project from ``{"name"}``."""
        body = _json_body(request)
        return {"project": self._store.rename_project(key, str(body.get("name", "")))}

    @_guard
    def remove_project(self, request: Any, key: str) -> dict[str, Any]:
        """Archive a project, or delete it with ``?force=1``."""
        return self._store.archive_project(key, _flag(request, "force"))

    # ---- board and entries ----------------------------------------------

    @_guard
    def board(self, request: Any) -> dict[str, Any]:
        """Return one project laid out as fixed status columns."""
        project = _query(request, "project")
        selected = self._store.get_project(project)
        entries = self._store.list_entries(project=project)
        columns = [
            {
                "status": status,
                "entries": [entry for entry in entries if entry["status"] == status],
            }
            for status in COLUMNS
        ]
        return {"project": selected, "columns": columns}

    @_guard
    def list_entries(self, request: Any) -> dict[str, Any]:
        """List entries with optional ``project``/``status`` filters."""
        return {
            "entries": self._store.list_entries(
                project=_query(request, "project"),
                status=_query(request, "status"),
                include_deleted=_flag(request, "include_deleted"),
            )
        }

    @_guard
    def create_entry(self, request: Any) -> tuple[dict[str, Any], int]:
        """Create an entry from a JSON object.

        Unknown fields are rejected, matching ``PATCH``: a timestamp in the
        body is an error rather than something silently dropped.
        """
        body = _json_body(request)
        _reject_unknown(body, WRITABLE_FIELDS)
        entry = self._store.create_entry(
            project=str(body.get("project", "")),
            title=str(body.get("title", "") or ""),
            content=_text(body.get("content")),
            status=str(body.get("status") or "todo"),
            priority=str(body.get("priority") or "medium"),
            due=_optional_text(body.get("due")),
            labels=body.get("labels"),
            assignee=_text(body.get("assignee")),
            links=body.get("links"),
        )
        return {"entry": entry}, 201

    @_guard
    def get_entry(self, request: Any, ref: str) -> dict[str, Any]:
        """Return one entry."""
        return {"entry": self._store.get_entry(ref)}

    @_guard
    def update_entry(self, request: Any, ref: str) -> dict[str, Any]:
        """Update any editable field in one transaction.

        Semantics, uniform across fields: an omitted key or ``null`` leaves
        the field unchanged, an empty string or empty list clears it, and
        ``title`` cannot be cleared.  Timestamps are rejected: they belong to
        the server.  ``status`` is validated together with the other fields,
        so a bad status leaves the entry untouched.
        """
        body = _json_body(request)
        allowed = WRITABLE_FIELDS - {"project"}
        _reject_unknown(body, allowed)
        if not body:
            raise BoardValidation("at least one field is required")
        if body.get("title", "x") is None:
            raise BoardValidation("title cannot be null; omit it to leave it unchanged")
        entry = self._store.update_entry(
            ref,
            title=None if body.get("title") is None else str(body["title"]),
            content=None if body.get("content") is None else str(body["content"]),
            status=None if body.get("status") is None else str(body["status"]),
            priority=None if body.get("priority") is None else str(body["priority"]),
            due=None if body.get("due") is None else str(body["due"]),
            labels=body.get("labels"),
            assignee=(None if body.get("assignee") is None else str(body["assignee"])),
            links=body.get("links"),
        )
        return {"entry": entry}

    @_guard
    def delete_entry(self, request: Any, ref: str) -> dict[str, Any]:
        """Soft-delete an entry."""
        return {"entry": self._store.delete_entry(ref)}
