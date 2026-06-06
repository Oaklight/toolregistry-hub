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

## Deployment Profiles

The `--profile` flag filters which tools are registered:

| Profile | Effect |
|---------|--------|
| `remote` | Disables server-local filesystem/shell/cron tools |
| `local` | Keeps only local-machine tools; disables network tools |
| *(none)* | All tools registered (default) |
