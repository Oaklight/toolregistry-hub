"""Board database path resolution.

One resolver serves both the MCP tool and the standalone admin process, so
the two processes cannot silently open different files.  The order is:

1. an explicit path (``PythonSource`` ``kwargs`` or ``--db``),
2. ``TOOLREGISTRY_HUB_BOARD_DB``,
3. ``$XDG_STATE_HOME/toolregistry-hub/board.sqlite3``,
4. ``~/.local/state/toolregistry-hub/board.sqlite3``.

The directory is created with mode ``0o700`` on first use, and the database
file is restricted to ``0o600`` by the store after it is written.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Environment variable that pins the database path for every process.
ENV_VAR = "TOOLREGISTRY_HUB_BOARD_DB"

#: Subdirectory under the XDG state home.
STATE_SUBDIR = "toolregistry-hub"

#: Database file name inside the state directory.
DB_FILENAME = "board.sqlite3"


def resolve_db_path(explicit: str | Path | None = None) -> Path:
    """Return the board database path.

    Args:
        explicit: A caller-supplied path, or ``None`` to fall through to the
            environment variable, the XDG state home, and ``~/.local/state``.

    Returns:
        The absolute, user-expanded path.  The parent directory is not
        created here; :class:`~toolregistry_hub.board.store.BoardStore`
        creates it when the first operation runs.
    """
    if explicit is not None and str(explicit):
        return Path(explicit).expanduser()

    env_value = os.environ.get(ENV_VAR)
    if env_value:
        return Path(env_value).expanduser()

    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        base = Path(state_home).expanduser()
    else:
        base = Path.home() / ".local" / "state"
    return base / STATE_SUBDIR / DB_FILENAME


__all__ = ["DB_FILENAME", "ENV_VAR", "STATE_SUBDIR", "resolve_db_path"]
