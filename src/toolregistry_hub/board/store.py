"""SQLite-backed project kanban store.

The store is the single writer-facing layer: the MCP tool, the admin
extension and the standalone admin process all go through it, so the status
vocabulary, the id scheme and the timestamp rules are defined once.

Design notes:

- One connection per operation.  MCP tool calls can arrive on worker
  threads, and a shared connection would need ``check_same_thread=False``
  plus a lock; WAL already gives the needed multi-thread and multi-process
  guarantees.
- Every timestamp is generated here with ``datetime.now(timezone.utc)``.
  No public method accepts a timestamp argument.
- Entry ids are ``<PROJECT_KEY>-<seq>``.  ``seq`` is allocated per project
  and never reused, so a deleted ``KAN-7`` cannot come back as a different
  row.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .paths import resolve_db_path

#: Canonical statuses, in board order.
STATUSES: tuple[str, ...] = ("backlog", "todo", "in_progress", "done", "cancelled")

#: Input spellings accepted for each canonical status.
STATUS_ALIASES: dict[str, str] = {
    "planned": "todo",
    "pending": "in_progress",
    "in-progress": "in_progress",
    "inprogress": "in_progress",
    "doing": "in_progress",
    "active": "in_progress",
    "complete": "done",
    "completed": "done",
    "closed": "done",
    "canceled": "cancelled",
}

#: Canonical priorities, most urgent first.
PRIORITIES: tuple[str, ...] = ("urgent", "high", "medium", "low")

#: Input spellings accepted for each priority.
PRIORITY_ALIASES: dict[str, str] = {
    "p0": "urgent",
    "p1": "high",
    "p2": "medium",
    "p3": "low",
    "normal": "medium",
    "minor": "low",
    "critical": "urgent",
}

#: Statuses that put an entry in a closed state.
CLOSED_STATUSES = frozenset({"done", "cancelled"})

#: Longest accepted entry title.
MAX_TITLE = 200

#: Longest accepted project key.
MAX_KEY = 10

_SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    next_seq    INTEGER NOT NULL DEFAULT 1,
    archived_at TEXT,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    content     TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'todo'
                CHECK (status IN ('backlog','todo','in_progress','done','cancelled')),
    priority    TEXT    NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low','medium','high','urgent')),
    due         TEXT,
    labels      TEXT    NOT NULL DEFAULT '[]',
    assignee    TEXT    NOT NULL DEFAULT '',
    links       TEXT    NOT NULL DEFAULT '[]',
    position    REAL    NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL,
    closed_at   TEXT,
    deleted_at  TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS entries_project_seq
    ON entries(project_id, seq);
CREATE INDEX IF NOT EXISTS entries_project_status
    ON entries(project_id, status, position, seq);
CREATE INDEX IF NOT EXISTS entries_deleted
    ON entries(deleted_at);
"""

_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,9}$")
_REF_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]{0,9})-(\d+)$")


class BoardError(ValueError):
    """Base class for board validation failures."""


class BoardValidation(BoardError):
    """A field value is not usable."""


class BoardConflict(BoardError):
    """A project key is already taken."""


class BoardNotFound(KeyError):
    """A project or entry reference does not exist."""

    def __str__(self) -> str:
        """Return the message without ``KeyError``'s quoting."""
        return str(self.args[0]) if self.args else "not found"


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        The timestamp with second precision, e.g. ``2026-11-19T02:00:00+00:00``.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_status(value: str) -> str:
    """Return the canonical status for *value*.

    Args:
        value: A canonical status or one of :data:`STATUS_ALIASES`.

    Returns:
        One of :data:`STATUSES`.

    Raises:
        BoardValidation: If the value is not recognised.
    """
    slug = str(value).strip().lower().replace(" ", "_")
    slug = STATUS_ALIASES.get(slug, slug)
    if slug not in STATUSES:
        raise BoardValidation(
            f"invalid status {value!r}; expected one of {', '.join(STATUSES)}"
        )
    return slug


def normalize_priority(value: str) -> str:
    """Return the canonical priority for *value*.

    Args:
        value: A canonical priority or one of :data:`PRIORITY_ALIASES`.

    Returns:
        One of :data:`PRIORITIES`.

    Raises:
        BoardValidation: If the value is not recognised.
    """
    slug = str(value).strip().lower()
    slug = PRIORITY_ALIASES.get(slug, slug)
    if slug not in PRIORITIES:
        raise BoardValidation(
            f"invalid priority {value!r}; expected one of {', '.join(PRIORITIES)}"
        )
    return slug


def normalize_due(value: str | None) -> str | None:
    """Validate a planned date and return it as ``YYYY-MM-DD``.

    The value is a planning field, not an audit timestamp: the caller picks
    it, and it takes part in no ordering or history decision.

    Args:
        value: An ISO date string, or ``None``/empty to clear the field.

    Returns:
        The date in ``YYYY-MM-DD`` form, or ``None``.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise BoardValidation(
            f"invalid due date {value!r}; expected YYYY-MM-DD"
        ) from exc


def normalize_title(value: str) -> str:
    """Validate and return an entry title.

    Args:
        value: The title text.

    Returns:
        The stripped title.

    Raises:
        BoardValidation: If the title is empty or too long.
    """
    text = str(value or "").strip()
    if not text:
        raise BoardValidation("title must not be empty")
    if len(text) > MAX_TITLE:
        raise BoardValidation(f"title must be at most {MAX_TITLE} characters")
    return text


def normalize_list(value: Iterable[str] | str | None, *, field: str) -> list[str]:
    """Normalise a list-valued field.

    Args:
        value: A list of strings, a comma-separated string, or ``None``.
        field: Field name used in the error message.

    Returns:
        A list of non-empty, stripped strings.

    Raises:
        BoardValidation: If a member is not a non-empty string.
    """
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = value.split(",")
    else:
        items = value
    result: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise BoardValidation(f"{field} members must be strings")
        text = item.strip()
        if text:
            result.append(text)
    return result


def normalize_links(value: Iterable[str] | str | None) -> list[str]:
    """Normalise the ``links`` field and reject non-HTTP schemes.

    Args:
        value: A list of URLs, a comma-separated string, or ``None``.

    Returns:
        The validated URLs.

    Raises:
        BoardValidation: If a URL does not start with ``http://`` or
            ``https://``.
    """
    links = normalize_list(value, field="links")
    for link in links:
        if not link.startswith(("http://", "https://")):
            raise BoardValidation(f"links must be http(s) URLs, got {link!r}")
    return links


def derive_key(name: str) -> str:
    """Derive a project key from a project name.

    The key is the initials of up to four words, upper-cased.  A name with
    no usable words falls back to ``PRJ``.

    Args:
        name: The project name.

    Returns:
        A key matching ``^[A-Z][A-Z0-9]{0,9}$``.
    """
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "PRJ"
    key = "".join(word[0] for word in words[:4]).upper()
    return key or "PRJ"


def _row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
    """Convert an ``entries`` row into the public entry shape."""
    return {
        "id": f"{row['key']}-{row['seq']}",
        "project": row["key"],
        "title": row["title"],
        "content": row["content"],
        "status": row["status"],
        "priority": row["priority"],
        "due": row["due"],
        "labels": json.loads(row["labels"] or "[]"),
        "assignee": row["assignee"],
        "links": json.loads(row["links"] or "[]"),
        "position": row["position"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "closed_at": row["closed_at"],
        "deleted_at": row["deleted_at"],
    }


class BoardStore:
    """Persistent project kanban backed by one SQLite file.

    The constructor is side-effect free: the directory, the connection and
    the schema are created by the first operation.  ``build_registry()``
    instantiates every tool class, so an eager constructor would create a
    database in the user's home on any import.

    Args:
        db: Explicit database path, or ``None`` to use
            :func:`~toolregistry_hub.board.paths.resolve_db_path`.
    """

    def __init__(self, db: str | Path | None = None) -> None:
        self._path = resolve_db_path(db)
        self._ready = False
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        """The database path this store uses."""
        return self._path

    # ---- connection management ------------------------------------------

    def _ensure_ready(self) -> None:
        """Create the directory, the schema, and harden permissions once."""
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            parent = self._path.parent
            created = not parent.exists()
            parent.mkdir(parents=True, exist_ok=True)
            if created:
                os.chmod(parent, 0o700)
            with sqlite3.connect(self._path, timeout=5.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.executescript(_SCHEMA)
                conn.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
            self._harden()
            self._ready = True

    def _harden(self) -> None:
        """Restrict the database and its WAL sidecars to the owner."""
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(f"{self._path}{suffix}")
            if candidate.exists():
                os.chmod(candidate, 0o600)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open one connection with the pragmas every operation needs."""
        self._ensure_ready()
        conn = sqlite3.connect(self._path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---- project helpers ------------------------------------------------

    def _find_project(self, conn: sqlite3.Connection, identifier: str) -> sqlite3.Row:
        """Resolve a project by key (case-insensitive) or exact name.

        Args:
            conn: The open connection.
            identifier: A project key or name.

        Returns:
            The project row.

        Raises:
            BoardNotFound: If no project matches.
        """
        text = str(identifier or "").strip()
        if not text:
            raise BoardValidation("project is required")
        row = conn.execute(
            "SELECT * FROM projects WHERE key = ? COLLATE NOCASE", (text,)
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT * FROM projects WHERE name = ?", (text,)
            ).fetchone()
        if row is None:
            raise BoardNotFound(f"unknown project {identifier!r}")
        return row

    @staticmethod
    def _parse_ref(ref: str) -> tuple[str, int]:
        """Split ``KAN-12`` into ``("KAN", 12)``.

        Args:
            ref: The entry reference.

        Returns:
            The upper-cased project key and the sequence number.

        Raises:
            BoardValidation: If the reference is malformed.
        """
        match = _REF_RE.match(str(ref or "").strip())
        if not match:
            raise BoardValidation(
                f"invalid entry reference {ref!r}; expected <KEY>-<number>, e.g. KAN-12"
            )
        return match.group(1).upper(), int(match.group(2))

    def _find_entry(self, conn: sqlite3.Connection, ref: str) -> sqlite3.Row:
        """Resolve an entry reference to a row, including deleted entries.

        Args:
            conn: The open connection.
            ref: The entry reference.

        Returns:
            A row joined with the project key.

        Raises:
            BoardNotFound: If the entry does not exist.
        """
        key, seq = self._parse_ref(ref)
        row = conn.execute(
            "SELECT e.*, p.key AS key FROM entries e "
            "JOIN projects p ON p.id = e.project_id "
            "WHERE p.key = ? COLLATE NOCASE AND e.seq = ?",
            (key, seq),
        ).fetchone()
        if row is None:
            raise BoardNotFound(f"unknown entry {ref!r}")
        return row

    # ---- projects --------------------------------------------------------

    def create_project(self, name: str, key: str = "") -> dict[str, Any]:
        """Create a project.

        Args:
            name: The project name.
            key: An explicit key, or empty to derive one from *name*.

        Returns:
            ``{"key", "name", "created_at"}``.

        Raises:
            BoardValidation: If the name is empty or the key is malformed.
            BoardConflict: If the key is taken.
        """
        text = str(name or "").strip()
        if not text:
            raise BoardValidation("project name must not be empty")
        with self._connect() as conn:
            if key:
                candidate = str(key).strip().upper()
                if not _KEY_RE.match(candidate):
                    raise BoardValidation(
                        f"invalid project key {key!r}; expected 1-{MAX_KEY} "
                        "alphanumeric characters starting with a letter"
                    )
            else:
                base = derive_key(text)
                candidate = base
                suffix = 2
                while conn.execute(
                    "SELECT 1 FROM projects WHERE key = ?", (candidate,)
                ).fetchone():
                    candidate = f"{base[: MAX_KEY - len(str(suffix))]}{suffix}"
                    suffix += 1
            if conn.execute(
                "SELECT 1 FROM projects WHERE key = ?", (candidate,)
            ).fetchone():
                raise BoardConflict(f"project key {candidate!r} already exists")
            now = utc_now()
            conn.execute(
                "INSERT INTO projects (key, name, next_seq, created_at, updated_at) "
                "VALUES (?, ?, 1, ?, ?)",
                (candidate, text, now, now),
            )
            return {"key": candidate, "name": text, "created_at": now}

    def list_projects(self, include_archived: bool = False) -> list[dict[str, Any]]:
        """Return projects with per-column entry counts.

        Args:
            include_archived: Include archived projects.

        Returns:
            One record per project: ``key``, ``name``, ``archived_at``,
            ``created_at`` and ``counts``.
        """
        with self._connect() as conn:
            where = "" if include_archived else "WHERE archived_at IS NULL"
            rows = conn.execute(
                f"SELECT * FROM projects {where} ORDER BY key"  # noqa: S608 - fixed clause
            ).fetchall()
            tallies: dict[int, dict[str, int]] = {}
            for row in conn.execute(
                "SELECT project_id, status, COUNT(*) AS n FROM entries "
                "WHERE deleted_at IS NULL GROUP BY project_id, status"
            ).fetchall():
                tallies.setdefault(row["project_id"], {})[row["status"]] = row["n"]
            result = []
            for row in rows:
                tally = dict.fromkeys(STATUSES, 0)
                tally.update(tallies.get(row["id"], {}))
                result.append(
                    {
                        "key": row["key"],
                        "name": row["name"],
                        "archived_at": row["archived_at"],
                        "created_at": row["created_at"],
                        "counts": tally,
                    }
                )
            return result

    def get_project(self, key: str) -> dict[str, Any]:
        """Return one project record.

        Args:
            key: Project key or exact name.

        Returns:
            ``key``, ``name``, ``archived_at``, ``created_at`` and
            ``updated_at``.

        Raises:
            BoardNotFound: If the project does not exist.
        """
        with self._connect() as conn:
            row = self._find_project(conn, key)
            return {
                "key": row["key"],
                "name": row["name"],
                "archived_at": row["archived_at"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def rename_project(self, key: str, name: str) -> dict[str, Any]:
        """Rename a project.

        Args:
            key: The project key or name.
            name: The new name.

        Returns:
            ``{"key", "name", "updated_at"}``.

        Raises:
            BoardNotFound: If the project does not exist.
            BoardValidation: If the name is empty.
        """
        text = str(name or "").strip()
        if not text:
            raise BoardValidation("project name must not be empty")
        with self._connect() as conn:
            row = self._find_project(conn, key)
            now = utc_now()
            conn.execute(
                "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
                (text, now, row["id"]),
            )
            return {"key": row["key"], "name": text, "updated_at": now}

    def archive_project(self, key: str, force: bool = False) -> dict[str, Any]:
        """Archive a project, or delete it and its entries with *force*.

        Args:
            key: The project key or name.
            force: Delete the project and every entry instead of archiving.

        Returns:
            ``{"key", "archived", "deleted_entries"}``.

        Raises:
            BoardNotFound: If the project does not exist.
        """
        with self._connect() as conn:
            row = self._find_project(conn, key)
            if force:
                total = conn.execute(
                    "SELECT COUNT(*) FROM entries WHERE project_id = ?",
                    (row["id"],),
                ).fetchone()[0]
                conn.execute("DELETE FROM projects WHERE id = ?", (row["id"],))
                return {
                    "key": row["key"],
                    "archived": False,
                    "deleted_entries": int(total),
                }
            now = utc_now()
            conn.execute(
                "UPDATE projects SET archived_at = ?, updated_at = ? WHERE id = ?",
                (now, now, row["id"]),
            )
            return {"key": row["key"], "archived": True, "deleted_entries": 0}

    # ---- entries ---------------------------------------------------------

    def create_entry(
        self,
        project: str,
        title: str,
        content: str = "",
        status: str = "todo",
        priority: str = "medium",
        due: str | None = None,
        labels: Iterable[str] | str | None = None,
        assignee: str = "",
        links: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        """Create an entry in a project.

        Args:
            project: The project key or name.
            title: The entry title.
            content: Free-form description.
            status: A status or status alias.
            priority: A priority or priority alias.
            due: An optional planned date, ``YYYY-MM-DD``.
            labels: A list of labels, or a comma-separated string.
            assignee: An optional assignee name.
            links: A list of http(s) URLs, or a comma-separated string.

        Returns:
            The created entry.

        Raises:
            BoardNotFound: If the project does not exist.
            BoardValidation: If a field is invalid.
        """
        title_text = normalize_title(title)
        status_value = normalize_status(status)
        priority_value = normalize_priority(priority)
        due_value = normalize_due(due)
        label_values = normalize_list(labels, field="labels")
        link_values = normalize_links(links)
        with self._connect() as conn:
            row = self._find_project(conn, project)
            now = utc_now()
            conn.execute("BEGIN IMMEDIATE")
            seq = conn.execute(
                "SELECT next_seq FROM projects WHERE id = ?", (row["id"],)
            ).fetchone()[0]
            conn.execute(
                "UPDATE projects SET next_seq = next_seq + 1 WHERE id = ?",
                (row["id"],),
            )
            conn.execute(
                "INSERT INTO entries (project_id, seq, title, content, status, "
                "priority, due, labels, assignee, links, position, created_at, "
                "updated_at, closed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",
                (
                    row["id"],
                    seq,
                    title_text,
                    str(content or ""),
                    status_value,
                    priority_value,
                    due_value,
                    json.dumps(label_values),
                    str(assignee or "").strip(),
                    json.dumps(link_values),
                    now,
                    now,
                    now if status_value in CLOSED_STATUSES else None,
                ),
            )
            entry = self._find_entry(conn, f"{row['key']}-{seq}")
            return _row_to_entry(entry)

    def get_entry(self, ref: str, include_deleted: bool = True) -> dict[str, Any]:
        """Return one entry.

        Args:
            ref: The entry reference, e.g. ``KAN-12``.
            include_deleted: Return soft-deleted entries as well.

        Returns:
            The entry.

        Raises:
            BoardNotFound: If the entry does not exist, or is deleted and
                *include_deleted* is false.
        """
        with self._connect() as conn:
            row = self._find_entry(conn, ref)
            if row["deleted_at"] and not include_deleted:
                raise BoardNotFound(f"entry {ref!r} is deleted")
            return _row_to_entry(row)

    def update_entry(
        self,
        ref: str,
        *,
        title: str | None = None,
        content: str | None = None,
        priority: str | None = None,
        due: str | None = None,
        labels: Iterable[str] | str | None = None,
        assignee: str | None = None,
        links: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        """Update entry fields.  ``None`` leaves a field unchanged.

        Passing an empty string clears a text field; passing an empty list
        clears a list field.

        Args:
            ref: The entry reference.
            title: A new title.
            content: New content.
            priority: A new priority or alias.
            due: A new planned date, or empty to clear it.
            labels: New labels.
            assignee: A new assignee, or empty to clear it.
            links: New links.

        Returns:
            The updated entry.

        Raises:
            BoardNotFound: If the entry does not exist.
            BoardValidation: If a field is invalid.
        """
        changes: dict[str, Any] = {}
        if title is not None:
            changes["title"] = normalize_title(title)
        if content is not None:
            changes["content"] = str(content)
        if priority is not None:
            changes["priority"] = normalize_priority(priority)
        if due is not None:
            changes["due"] = normalize_due(due)
        if labels is not None:
            changes["labels"] = json.dumps(normalize_list(labels, field="labels"))
        if assignee is not None:
            changes["assignee"] = str(assignee).strip()
        if links is not None:
            changes["links"] = json.dumps(normalize_links(links))
        with self._connect() as conn:
            row = self._find_entry(conn, ref)
            if row["deleted_at"]:
                raise BoardNotFound(f"entry {ref!r} is deleted")
            if not changes:
                return _row_to_entry(row)
            changes["updated_at"] = utc_now()
            assignments = ", ".join(f"{column} = ?" for column in changes)
            conn.execute(
                f"UPDATE entries SET {assignments} WHERE id = ?",  # noqa: S608 - fixed columns
                (*changes.values(), row["id"]),
            )
            return _row_to_entry(self._find_entry(conn, ref))

    def update_status(self, ref: str, status: str) -> dict[str, Any]:
        """Move an entry to another column.

        Args:
            ref: The entry reference.
            status: A status or status alias.

        Returns:
            The updated entry.

        Raises:
            BoardNotFound: If the entry does not exist.
            BoardValidation: If the status is invalid.
        """
        value = normalize_status(status)
        with self._connect() as conn:
            row = self._find_entry(conn, ref)
            if row["deleted_at"]:
                raise BoardNotFound(f"entry {ref!r} is deleted")
            now = utc_now()
            closed = now if value in CLOSED_STATUSES else None
            conn.execute(
                "UPDATE entries SET status = ?, updated_at = ?, closed_at = ? "
                "WHERE id = ?",
                (value, now, closed, row["id"]),
            )
            return _row_to_entry(self._find_entry(conn, ref))

    def delete_entry(self, ref: str) -> dict[str, Any]:
        """Soft-delete an entry.

        Args:
            ref: The entry reference.

        Returns:
            ``{"id", "project", "deleted", "deleted_at"}``.

        Raises:
            BoardNotFound: If the entry does not exist or is already deleted.
        """
        with self._connect() as conn:
            row = self._find_entry(conn, ref)
            if row["deleted_at"]:
                raise BoardNotFound(f"entry {ref!r} is already deleted")
            now = utc_now()
            conn.execute(
                "UPDATE entries SET deleted_at = ?, updated_at = ? WHERE id = ?",
                (now, now, row["id"]),
            )
            return {
                "id": f"{row['key']}-{row['seq']}",
                "project": row["key"],
                "deleted": True,
                "deleted_at": now,
            }

    def list_entries(
        self,
        project: str = "",
        status: str = "",
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        """Return entries, optionally filtered.

        Args:
            project: A project key or name, or empty for every project.
            status: A status or alias, or empty for every column.
            include_deleted: Include soft-deleted entries.

        Returns:
            The matching entries, ordered by project key and sequence.
        """
        clauses: list[str] = []
        params: list[Any] = []
        if project:
            with self._connect() as conn:
                row = self._find_project(conn, project)
            clauses.append("e.project_id = ?")
            params.append(row["id"])
        if status:
            clauses.append("e.status = ?")
            params.append(normalize_status(status))
        if not include_deleted:
            clauses.append("e.deleted_at IS NULL")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT e.*, p.key AS key FROM entries e "
                "JOIN projects p ON p.id = e.project_id "
                f"{where} ORDER BY p.key, e.position, e.seq",  # noqa: S608 - fixed clauses
                params,
            ).fetchall()
            return [_row_to_entry(row) for row in rows]
