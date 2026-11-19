---
title: Admin Panel
summary: Run the ToolRegistry admin panel and the Kanban tab as a standalone service
description: The toolregistry-hub admin command serves the core admin panel from its own process and mounts the Kanban extension. It shares one SQLite file with the MCP daemon, so tools and people see the same board.
keywords: admin panel, kanban, standalone service, systemd, token, board
author: Oaklight
---

# Admin Panel

`toolregistry-hub admin` serves the ToolRegistry admin panel from a separate
process. The MCP server and the panel are independent: restarting one does not
interrupt the other, and the panel stays up while a session reconnects.

The panel always mounts the **Kanban** tab, backed by the same SQLite file the
`board-*` MCP tools write to.

## Command

```bash
toolregistry-hub admin \
  --host 127.0.0.1 \
  --port 8081 \
  --config ~/.config/toolregistry-hub/tools-local.jsonc \
  --db ~/.local/state/toolregistry-hub/board.sqlite3 \
  --token-file ~/.config/toolregistry-hub/admin-token
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8081` | Bind port; a busy port makes the panel pick another and log the URL |
| `--token` | — | Bearer token for the panel |
| `--token-file` | — | Read the token from the first non-empty line |
| `--config` | discovered preset | Tool config to load for the panel's tool pages |
| `--db` | shared default | Board database path |
| `--no-banner` | off | Skip the Hub banner |

Rules:

- `--token` and `--token-file` are mutually exclusive.
- A non-loopback `--host` without a token is refused: the panel exposes a
  writable board.

The token must be generated once and stored with `0600` permissions:

```bash
install -m 600 /dev/null ~/.config/toolregistry-hub/admin-token
python -c 'import secrets; print(secrets.token_hex(24))' \
  > ~/.config/toolregistry-hub/admin-token
```

The panel's HTML shell and assets load without a token; every `/api/*` and
`/ext/board/*` call requires it. The browser asks for the token once and keeps
a session cookie.

## systemd user unit

```ini
[Unit]
Description=ToolRegistry Hub kanban admin panel (127.0.0.1:8081)
After=network.target toolregistry-hub-mcp.service
Wants=toolregistry-hub-mcp.service

[Service]
Type=simple
WorkingDirectory=/home/pding
UMask=0077
Environment=TOOLREGISTRY_HUB_BOARD_DB=/home/pding/.local/state/toolregistry-hub/board.sqlite3
ExecStartPre=/usr/bin/install -d -m 700 /home/pding/.local/state/toolregistry-hub
ExecStart=/path/to/toolregistry-hub admin --host 127.0.0.1 --port 8081 \
    --config /home/pding/.config/toolregistry-hub/tools-local.jsonc \
    --db /home/pding/.local/state/toolregistry-hub/board.sqlite3 \
    --token-file /home/pding/.config/toolregistry-hub/admin-token
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now toolregistry-hub-admin
journalctl --user -u toolregistry-hub-admin -n 30 --no-pager
```

Add the same `TOOLREGISTRY_HUB_BOARD_DB` to the MCP unit. If the two processes
resolve different paths, two independent boards appear with no error.

## Kanban tab

The tab shows one project at a time:

- project selector, **New project**, **Refresh**;
- five columns, always present, even when empty;
- cards show id, title, content, priority, due date, assignee, labels and links;
- the status selector on a card moves it between columns;
- **Edit** opens an inline form for every editable field;
- **Delete** soft-deletes the entry after a confirmation;
- every column has an **Add entry** form pre-filled with that column's status.

Drag and drop is not implemented in this version. The entries table reserves a
`position` column for it.

## API

The tab talks to these routes under `/ext/board`:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/projects` | Projects with per-column counts |
| POST | `/projects` | Create a project |
| PATCH | `/projects/<key>` | Rename |
| DELETE | `/projects/<key>?force=1` | Archive, or delete with `force` |
| GET | `/board?project=KAN` | Five fixed columns with entries |
| GET | `/entries?project=&status=&include_deleted=` | Filtered entries |
| POST | `/entries` | Create an entry |
| GET | `/entries/<ref>` | One entry |
| PATCH | `/entries/<ref>` | Update editable fields |
| DELETE | `/entries/<ref>` | Soft delete |
| GET | `/meta` | Schema version and, on loopback, the database path |

Both write routes reject unknown fields, so `created_at`, `updated_at`,
`closed_at` and `deleted_at` are refused rather than silently dropped.

`PATCH` field semantics are uniform: an omitted key or `null` leaves the field
unchanged, an empty string or empty list clears it, and `title` cannot be
cleared. `status` is validated together with the other fields, so a request
carrying a bad status writes nothing. A storage failure answers 503 with the
panel's JSON error shape.

## See also

- [Kanban Board Tool](../tools/board.md)
- [Server guide](../server.md)
