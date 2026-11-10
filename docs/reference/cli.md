---
title: CLI Reference
summary: Complete command-line interface reference for toolregistry-hub
description: All CLI commands, flags, and options for the toolregistry-hub launcher.
keywords: cli, command line, options, flags, openapi, mcp, local-hub, hub-shim, keys
author: Oaklight
---

# CLI Reference

`toolregistry-hub` is a launcher for `toolregistry-server`. It resolves the
tool preset, translates the Hub command into the equivalent server command,
and runs the server CLI with the Hub application object.

## Synopsis

```
toolregistry-hub [OPTIONS] COMMAND [COMMAND-OPTIONS]
```

Hub-only options are accepted before or after the command.

## Launcher behaviour

- **Preset.** An explicit `--config PATH` (or `--config=PATH`) wins; otherwise
  `TOOLS_CONFIG`, then `tools.jsonc` / `tools.yaml` / `tools.yml` in the
  working directory, then the packaged `data/tools.yaml`. The resolved file is
  passed to the server as `--config` when the command needs one. The packaged
  preset stays memory-only: a runtime source change never rewrites it.
- **Translation.** The Hub command is rewritten before the server parses it:

| Hub command | Server command |
|-------------|----------------|
| `openapi` | `gateway --openapi` |
| `mcp --transport streamable-http` or `http` | `gateway --mcp` |
| `mcp --transport sse` | `gateway --sse` |
| `mcp` (stdio or no transport) | `mcp --transport stdio` |
| `gateway`, `local-hub`, `hub-shim`, `keys` | unchanged |

- `--backend` is forwarded to the gateway for `openapi` and the HTTP MCP
  transports, and dropped for stdio, where it has no meaning.
- The launcher prints the Hub banner and update check itself (the server
  banner is suppressed) and sets `TOOLREGISTRY_LOCAL_HUB_COMMAND=toolregistry-hub`
  before starting the server. The foreground process always runs the Hub app,
  so `local-hub run` is unaffected. toolregistry-server 0.9.0 does not read the
  variable, so a hub it starts as a detached process (`local-hub ensure`, or
  `hub-shim` without `--no-spawn`) is `toolregistry-server local-hub run
  --config <preset>`: the preset tools are served because the server loads the
  Python sources, but the Hub-only helpers (discovery helpers,
  `toolcall_reason` injection, admin panel) are not applied to that process.
  The launcher prints a warning on stderr in that case.
- `toolregistry-hub <command> --help` shows the server options for the
  translated command; `toolregistry-hub --help` lists the Hub commands and
  flags.

## Global Options

| Flag | Description |
|------|-------------|
| `--version` / `-V` | Show the Hub version (with update check) and exit |
| `--no-banner` | Disable the startup banner |

## Hub Options

| Flag | Default | Description |
|------|---------|-------------|
| `--admin-port PORT` | — | Enable the core admin panel on this port |
| `--tool-discovery` / `--no-tool-discovery` | enabled | Progressive tool disclosure via `discover_tools` |
| `--think-augment` / `--no-think-augment` | enabled | Inject `toolcall_reason` property into tool schemas |

## Commands

### `openapi`

Start an OpenAPI (REST) server through the gateway, with only the OpenAPI
frontend enabled. The default backend is FastAPI; `--backend httpserver`
selects the zero-dependency backend.

```bash
toolregistry-hub openapi [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host HOST` | `0.0.0.0` | Bind address |
| `--port PORT` | `8000` | Bind port |
| `--backend {fastapi,httpserver}` | `fastapi` | OpenAPI server backend; `httpserver` is the zero-dependency backend |
| `--env PATH` | `.env` | Path to `.env` file |
| `--no-env` | — | Skip loading `.env` |
| `--config PATH` | resolved preset | Tool configuration file (JSON, JSONC, or YAML) |
| `--tokens PATH` | — | Bearer token file (one per line) |
| `--profile {remote,local}` | none | Deployment profile filter (see below) |
| `--config-reload` / `--no-config-reload` | disabled | Reload the config file when it changes |
| `--reload` | — | Auto-reload for development |

### `mcp`

Start an MCP (Model Context Protocol) server.

`--transport stdio` (the default) is served directly by the MCP server: the
gateway has no stdio frontend. The HTTP transports (`streamable-http`, `http`
and `sse`) are served through the gateway.

```bash
toolregistry-hub mcp [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--transport {stdio,sse,streamable-http}` | `stdio` | MCP transport type |
| `--host HOST` | `127.0.0.1` | Bind address (SSE / streamable-http only) |
| `--port PORT` | `8000` | Bind port (SSE / streamable-http only) |
| `--env PATH` | `.env` | Path to `.env` file |
| `--no-env` | — | Skip loading `.env` |
| `--config PATH` | resolved preset | Tool configuration file (JSON, JSONC, or YAML) |
| `--profile {remote,local}` | none | Deployment profile filter (see below) |
| `--config-reload` / `--no-config-reload` | disabled | Reload the config file when it changes |

### `gateway`

Serve OpenAPI and MCP from one process. This is the server command; use
`toolregistry-hub gateway --help` for its full option set.

```bash
toolregistry-hub gateway [OPTIONS]
```

### `local-hub`

Run one resident gateway shared by local clients. POSIX only.

```bash
toolregistry-hub local-hub [run|ensure|stop|status] [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `action` | `run` | `run` serves in the foreground; `ensure` starts a detached hub and prints its endpoint; `stop` signals the hub; `status` reports it |
| `--name NAME` | `default` | Hub name |
| `--idle-timeout SECONDS` | `0` | Exit after this many seconds without a request or an open MCP session; `0` stays resident |
| `--timeout SECONDS` | — | Wait limit for `ensure` and `stop` |
| `--json` | — | Print status as JSON |
| `--keys-db PATH` | — | Inbound key store; mandatory for a hub started this way |

The launcher sets `TOOLREGISTRY_LOCAL_HUB_COMMAND=toolregistry-hub` before
running the server, so a server that reads the variable starts a detached hub
through the Hub launcher with the resolved preset. toolregistry-server 0.9.0
ignores it: a hub it starts detached is then `toolregistry-server local-hub run
--config <preset>`, which serves the preset tools (the server loads the Python
sources) but does not apply the Hub-only helpers (discovery helpers,
`toolcall_reason` injection, admin panel). The launcher warns on stderr when it
expects a detached hub and the installed server does not read the variable.
The `run` action is unaffected: it serves in the launcher process with the Hub
app.

### `hub-shim`

Expose one local hub to a stdio MCP client. POSIX only.

```bash
toolregistry-hub hub-shim [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--name NAME` | `default` | Hub to attach to |
| `--key-file PATH` | — | File holding the client key; falls back to `TOOLREGISTRY_HUB_KEY` |
| `--connect-timeout SECONDS` | `5` | Limit for one connection attempt |
| `--no-spawn` | — | Never start a hub; report it as unavailable instead |
| `--config PATH` | resolved preset | Config used when the shim has to start the hub |
| `--socket PATH` | — | Unix socket for a hub the shim starts |
| `--keys-db PATH` | — | Key store a hub the shim starts must use |

### `keys`

Manage inbound API keys (`create`, `list`, `get`, `revoke`,
`set-concurrency`). `keys` requires `--db PATH`; `set-concurrency` takes
`--value N` or `--clear`. The command passes through to the server unchanged.

```bash
toolregistry-hub keys <subcommand> [OPTIONS]
```

### Config hot reload

With `--config-reload`, the server starts a background watcher that polls the
config file (`--config`) and applies a source-level diff to the running
registry: an added source is registered, a removed source is unregistered, a
source that leaves the configured scope is disabled, and a changed
declaration is replaced. A malformed file is logged and ignored, and the
current registry keeps serving. Default metadata is applied only to the tools
a reload registers, so an existing tool keeps a value changed from the admin
panel. The deployment profile is applied again to each source a reload
registers, so tools it excludes stay disabled. The watcher is opt-in and per
process; it does not coordinate between services.

Known limitation: removing a `tool_metadata` entry from the file does not
revert the value it set until the process restarts. The same fields are
writable from the admin panel, so a reload cannot tell a file-applied value
from a later panel edit. Reset the field from the panel if needed.

A source that registers successfully but produces no tools is not pulled
again while its declaration stays unchanged. If an MCP server advertises its
tools only later, change the source declaration (or restart the process) to
register them.

## Deployment Profiles

The `--profile` flag filters which tools are registered:

| Profile | Effect |
|---------|--------|
| `remote` | Disables server-local filesystem/shell/cron tools |
| `local` | Keeps only local-machine tools; disables network tools |
| *(none)* | All tools registered (default) |
