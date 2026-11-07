---
title: CLI Reference
summary: Complete command-line interface reference for toolregistry-hub
description: All CLI commands, flags, and options for the toolregistry-hub server.
keywords: cli, command line, options, flags, openapi, mcp
author: Oaklight
---

# CLI Reference

The `toolregistry-hub` command launches the hub server in OpenAPI or MCP mode.

## Synopsis

```
toolregistry-hub [OPTIONS] COMMAND [COMMAND-OPTIONS]
```

## Global Options

| Flag | Description |
|------|-------------|
| `--version` / `-V` | Show version and exit |
| `--no-banner` | Disable the startup banner |

## Commands

### `openapi`

Start an OpenAPI (REST) server powered by FastAPI.

```bash
toolregistry-hub openapi [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host HOST` | `0.0.0.0` | Bind address |
| `--port PORT` | `8000` | Bind port |
| `--env PATH` | `.env` | Path to `.env` file |
| `--no-env` | — | Skip loading `.env` |
| `--config PATH` | — | Tool configuration file (JSON, JSONC, or YAML) |
| `--tokens PATH` | — | Bearer token file (one per line) |
| `--admin-port PORT` | — | Enable admin panel on this port |
| `--tool-discovery` / `--no-tool-discovery` | enabled | Progressive tool disclosure via `discover_tools` |
| `--think-augment` / `--no-think-augment` | enabled | Inject `toolcall_reason` property into tool schemas |
| `--profile {remote,local}` | none | Deployment profile filter (see below) |
| `--config-reload` / `--no-config-reload` | disabled | Reload the config file when it changes (poll-based, per process; #144) |
| `--reload` | — | Auto-reload for development |

### `mcp`

Start an MCP (Model Context Protocol) server.

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
| `--config PATH` | — | Tool configuration file (JSON, JSONC, or YAML) |
| `--admin-port PORT` | — | Enable admin panel on this port |
| `--tool-discovery` / `--no-tool-discovery` | enabled | Progressive tool disclosure via `discover_tools` |
| `--think-augment` / `--no-think-augment` | enabled | Inject `toolcall_reason` property into tool schemas |
| `--profile {remote,local}` | none | Deployment profile filter (see below) |
| `--config-reload` / `--no-config-reload` | disabled | Reload the config file when it changes (poll-based, per process; #144) |

### Config hot reload

With `--config-reload`, `openapi` and `mcp` start a background watcher that
polls the config file (`--config`) and applies a source-level diff to the
running registry: an added source is registered, a removed source is
unregistered, a source that leaves the configured scope is disabled, and a
changed declaration is replaced. A malformed file is logged and ignored, and
the current registry keeps serving. Hub default metadata (`tags`, `defer`,
`title`, `search_hint` and the execution hints) is applied only to the tools a
reload registers, so an existing tool keeps a value changed from the admin
panel. The watcher is opt-in and per process; it does not coordinate between
services.

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
