"""Persistent project kanban tools.

The class exposes one MCP namespace, ``board``.  Every method delegates to
:class:`~toolregistry_hub.board.store.BoardStore`; this module owns only the
argument surface, the markdown rendering and the metadata declarations.

All timestamps are produced by the store.  No tool accepts a
``created_at``/``updated_at`` style argument, so a caller cannot forge the
audit history.  ``due`` is a planning date and is the only date the caller
chooses.
"""

from __future__ import annotations

from typing import Any, TypedDict, cast

from toolregistry import ToolTag

from .._metadata import tool_metadata
from .store import STATUSES, BoardStore, normalize_status

#: Column headings used by the markdown renderers.
_COLUMN_LABELS = {
    "backlog": "Backlog",
    "todo": "To do",
    "in_progress": "In progress",
    "done": "Done",
    "cancelled": "Cancelled",
}

#: Preview length for entry content in tables.
_PREVIEW = 80


class ProjectCreated(TypedDict, total=False):
    """Result of ``BoardTools.create_project``."""

    key: str
    name: str
    created_at: str


class ProjectArchived(TypedDict, total=False):
    """Result of ``BoardTools.archive_project``."""

    key: str
    archived: bool
    deleted_entries: int


class EntryResult(TypedDict, total=False):
    """Result of the entry create/read/update methods."""

    id: str
    project: str
    title: str
    content: str
    status: str
    priority: str
    due: str | None
    labels: list[str]
    assignee: str
    links: list[str]
    position: float
    created_at: str
    updated_at: str
    closed_at: str | None
    deleted_at: str | None


class EntryDeleted(TypedDict, total=False):
    """Result of ``BoardTools.delete_entry``."""

    id: str
    project: str
    deleted: bool
    deleted_at: str


def _entry_schema() -> dict[str, Any]:
    """Return the JSON schema shared by the entry-returning tools."""
    return {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "project": {"type": "string"},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "status": {"type": "string"},
            "priority": {"type": "string"},
            "due": {"type": ["string", "null"]},
            "labels": {"type": "array", "items": {"type": "string"}},
            "assignee": {"type": "string"},
            "links": {"type": "array", "items": {"type": "string"}},
            "position": {"type": "number"},
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "closed_at": {"type": ["string", "null"]},
            "deleted_at": {"type": ["string", "null"]},
        },
        "additionalProperties": True,
    }


def _escape(text: Any) -> str:
    """Escape a markdown table cell."""
    return str(text if text is not None else "").replace("|", "\\|")


def _preview(text: str, limit: int = _PREVIEW) -> str:
    """Collapse whitespace and shorten *text* for a table cell."""
    flat = " ".join(str(text or "").split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "…"


def _render_entries(entries: list[dict[str, Any]]) -> str:
    """Render entries as a markdown table."""
    if not entries:
        return "No entries."
    lines = [
        "| id | project | status | priority | title | due | assignee | labels |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(entry["id"]),
                    _escape(entry["project"]),
                    _escape(entry["status"]),
                    _escape(entry["priority"]),
                    _escape(entry["title"]),
                    _escape(entry["due"]),
                    _escape(entry["assignee"]),
                    _escape(", ".join(entry["labels"])),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _render_board(project: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    """Render one project as a column-per-heading markdown board."""
    by_status: dict[str, list[dict[str, Any]]] = {status: [] for status in STATUSES}
    for entry in entries:
        by_status.setdefault(entry["status"], []).append(entry)
    lines = [f"# {project['key']} — {project['name']}", ""]
    for status in STATUSES:
        column = by_status.get(status, [])
        lines.append(f"## {_COLUMN_LABELS[status]} ({len(column)})")
        if not column:
            lines.append("_empty_")
        for entry in column:
            meta = [entry["priority"]]
            if entry["due"]:
                meta.append(f"due {entry['due']}")
            if entry["assignee"]:
                meta.append(f"@{entry['assignee']}")
            if entry["labels"]:
                meta.append(", ".join(entry["labels"]))
            lines.append(f"- **{entry['id']}** {entry['title']} _({' · '.join(meta)})_")
            if entry["content"]:
                lines.append(f"  {_preview(entry['content'], 160)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


class BoardTools:
    """Project kanban with create/update/delete entry operations.

    Args:
        db: Explicit SQLite path.  ``None`` resolves to the shared default
            (see :mod:`toolregistry_hub.board.paths`).  The constructor
            creates nothing; the first tool call opens the database.
    """

    def __init__(self, db: str | None = None) -> None:
        self._store = BoardStore(db)

    @property
    def db_path(self) -> str:
        """The resolved database path."""
        return str(self._store.path)

    # ---- projects --------------------------------------------------------

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM},
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
        defer=True,
        title="Create Board Project",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "name": {"type": "string"},
                    "created_at": {"type": "string"},
                },
                "additionalProperties": True,
            }
        },
    )
    def create_project(self, name: str, key: str = "") -> ProjectCreated:
        """Create a project that entries can be filed under.

        Args:
            name: Human-readable project name.
            key: Optional uppercase key (1-10 alphanumerics, starting with a
                letter) used in entry ids such as ``KAN-12``.  Empty derives
                one from the name.

        Returns:
            ``key``, ``name`` and the server-generated ``created_at``.
        """
        return cast(ProjectCreated, self._store.create_project(name, key))

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="List Board Projects",
    )
    def list_projects(self) -> str:
        """List projects and how many entries each has per column.

        Returns:
            A markdown table, or a sentence when no project exists.
        """
        projects = self._store.list_projects()
        if not projects:
            return "No projects yet. Create one with board-create_project."
        lines = [
            "| key | name | backlog | todo | in_progress | done | cancelled |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for project in projects:
            counts = project["counts"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape(project["key"]),
                        _escape(project["name"]),
                        *(str(counts[status]) for status in STATUSES),
                    ]
                )
                + " |"
            )
        return "\n".join(lines)

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM, ToolTag.DESTRUCTIVE},
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="Archive Board Project",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "archived": {"type": "boolean"},
                    "deleted_entries": {"type": "integer"},
                },
                "additionalProperties": True,
            }
        },
    )
    def archive_project(self, key: str, force: bool = False) -> ProjectArchived:
        """Archive a project, or delete it and all its entries.

        Args:
            key: Project key or exact name.
            force: Delete the project and its entries instead of archiving.
                Archived projects keep their entries and can be listed with
                ``include_archived``; deletion is irreversible.

        Returns:
            ``key``, whether it was archived, and how many entries were
            deleted.
        """
        return cast(ProjectArchived, self._store.archive_project(key, force))

    # ---- entries ---------------------------------------------------------

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM},
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
        defer=True,
        title="Create Board Entry",
        extra={"output_schema": _entry_schema()},
    )
    def create_entry(
        self,
        project: str,
        title: str,
        content: str = "",
        status: str = "todo",
        priority: str = "medium",
        due: str = "",
        labels: list[str] | str | None = None,
        assignee: str = "",
        links: list[str] | str | None = None,
    ) -> EntryResult:
        """Create an entry in a project.

        Args:
            project: Project key or exact name.
            title: Short summary shown on the card.
            content: Free-form detail.
            status: One of ``backlog | todo | in_progress | done |
                cancelled``.  Aliases ``planned`` (→ todo), ``pending`` /
                ``doing`` / ``active`` (→ in_progress), ``completed`` /
                ``closed`` (→ done), ``canceled`` (→ cancelled) are accepted.
            priority: One of ``urgent | high | medium | low``; ``p0``-``p3``
                are accepted as aliases.
            due: Optional planned date, ``YYYY-MM-DD``.  This is a planning
                field only; all timestamps are set by the server.
            labels: Labels as a list or a comma-separated string.
            assignee: Optional owner name.
            links: Related http(s) URLs as a list or comma-separated string.

        Returns:
            The created entry, including its ``<KEY>-<n>`` id.
        """
        return cast(
            EntryResult,
            self._store.create_entry(
                project=project,
                title=title,
                content=content,
                status=status,
                priority=priority,
                due=due,
                labels=labels,
                assignee=assignee,
                links=links,
            ),
        )

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="Get Board Entry",
        extra={"output_schema": _entry_schema()},
    )
    def get_entry(self, ref: str) -> EntryResult:
        """Return one entry by reference.

        Args:
            ref: Entry id such as ``KAN-12`` (case-insensitive).

        Returns:
            The full entry, including soft-deleted ones so a stale reference
            resolves to a clear answer instead of an error.
        """
        return cast(EntryResult, self._store.get_entry(ref))

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM},
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="Update Board Entry",
        extra={"output_schema": _entry_schema()},
    )
    def update_entry(
        self,
        ref: str,
        title: str | None = None,
        content: str | None = None,
        priority: str | None = None,
        due: str | None = None,
        labels: list[str] | str | None = None,
        assignee: str | None = None,
        links: list[str] | str | None = None,
    ) -> EntryResult:
        """Update entry fields; omitted fields are left unchanged.

        Args:
            ref: Entry id such as ``KAN-12``.
            title: New title.
            content: New content; an empty string clears it.
            priority: New priority or alias.
            due: New planned date ``YYYY-MM-DD``; an empty string clears it.
            labels: New labels; an empty list clears them.
            assignee: New owner; an empty string clears it.
            links: New links; an empty list clears them.

        Returns:
            The updated entry with a refreshed ``updated_at``.
        """
        return cast(
            EntryResult,
            self._store.update_entry(
                ref,
                title=title,
                content=content,
                priority=priority,
                due=due,
                labels=labels,
                assignee=assignee,
                links=links,
            ),
        )

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM},
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="Update Board Status",
        extra={"output_schema": _entry_schema()},
    )
    def update_status(self, ref: str, status: str) -> EntryResult:
        """Move an entry to another column.

        Args:
            ref: Entry id such as ``KAN-12``.
            status: The destination status or a documented alias.

        Returns:
            The updated entry.  ``closed_at`` changes only on a transition:
            entering ``done`` or ``cancelled`` stamps it, staying in that
            state keeps the original value, and reopening clears it.
        """
        return cast(EntryResult, self._store.update_status(ref, status))

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM, ToolTag.DESTRUCTIVE},
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="Delete Board Entry",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "project": {"type": "string"},
                    "deleted": {"type": "boolean"},
                    "deleted_at": {"type": "string"},
                },
                "additionalProperties": True,
            }
        },
    )
    def delete_entry(self, ref: str) -> EntryDeleted:
        """Soft-delete an entry.

        A deleted entry keeps its id and its history.  The sequence number is
        never reused: a project force-deleted and recreated with the same key
        continues from the retired sequence, so an old ref cannot resolve to
        a different entry.  Deleting twice is an error rather than a silent
        no-op, so a mistyped reference is visible.

        Args:
            ref: Entry id such as ``KAN-12``.

        Returns:
            ``id``, ``project``, ``deleted`` and the server-generated
            ``deleted_at``.
        """
        return cast(EntryDeleted, self._store.delete_entry(ref))

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="List Board Entries",
    )
    def list_entries(
        self,
        project: str = "",
        status: str = "",
        include_deleted: bool = False,
    ) -> str:
        """List entries as a table.

        Args:
            project: Project key or name; empty includes every project.
            status: Status or alias; empty includes every column.
            include_deleted: Also list soft-deleted entries.

        Returns:
            A markdown table, or a sentence when nothing matches.
        """
        entries = self._store.list_entries(
            project=project, status=status, include_deleted=include_deleted
        )
        return _render_entries(entries)

    @tool_metadata(
        tags={ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
        defer=True,
        title="View Board",
    )
    def view(self, project: str = "") -> str:
        """Render one project as a kanban board.

        Args:
            project: Project key or exact name.  When empty and exactly one
                project exists, that project is used; otherwise an error
                lists the available keys.

        Returns:
            Markdown with one section per column.
        """
        projects = self._store.list_projects()
        if not project:
            if len(projects) == 1:
                project = projects[0]["key"]
            elif not projects:
                return "No projects yet. Create one with board-create_project."
            else:
                keys = ", ".join(item["key"] for item in projects)
                raise ValueError(f"project is required; available projects: {keys}")
        chosen = self._store.get_project(project)
        entries = self._store.list_entries(project=project)
        return _render_board(chosen, entries)


__all__ = [
    "BoardTools",
    "EntryDeleted",
    "EntryResult",
    "ProjectArchived",
    "ProjectCreated",
]

# ``normalize_status`` is re-exported for the admin extension's assertions.
_ = normalize_status
