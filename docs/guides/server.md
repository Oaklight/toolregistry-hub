---
title: Server Configuration
summary: Configure authentication, tool loading, and custom tool registration
description: Set up Bearer Token authentication, control which tools are loaded, register custom tools, and deploy with profiles.
keywords: server, configuration, authentication, tools.jsonc, custom tools, profiles
author: Oaklight
---

# Server Configuration

This guide covers authentication, tool selection, custom tool registration, and deployment profiles. For launching a server, see **[Launch a Server](../get-started/server.md)**.

## Authentication

The server supports optional Bearer Token authentication.

### Setup

=== "Single Token"

    ```bash
    export API_BEARER_TOKEN="your-secret-token"
    ```

=== "Multiple Tokens"

    ```bash
    export API_BEARER_TOKEN="token1,token2,token3"
    ```

=== "Token File"

    ```bash
    export API_BEARER_TOKENS_FILE="/path/to/tokens.txt"
    ```

    One token per line in the file.

### Usage

```http
Authorization: Bearer your-valid-token
```

If no token variables are set, authentication is disabled.

You can also pass a token file directly via CLI:

```bash
toolregistry-hub openapi --tokens /path/to/tokens.txt
```

## Tool Configuration

Control which tools are loaded with a `tools.jsonc` file:

```bash
# Auto-discovered from working directory
cp tools.jsonc.example tools.jsonc

# Or specify via CLI
toolregistry-hub openapi --config path/to/tools.jsonc
```

### Denylist Mode (Default)

Load all tools except those explicitly disabled:

```jsonc
{
  "mode": "denylist",
  "disabled": ["file_ops"]  // disable specific tools
}
```

### Allowlist Mode

Load only the tools you specify:

```jsonc
{
  "mode": "allowlist",
  "enabled": ["calculator", "datetime", "unit_converter"]
}
```

## Custom Tool Registration

You can register your own tool classes alongside the built-in tools:

```jsonc
{
  "tools": [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "my_package.MyTool", "namespace": "my_tool"}
  ]
}
```

Custom classes must follow the same interface as built-in tools. Each tool class is imported and registered under the given namespace.

## Deployment Profiles

The `--profile` flag filters which tools are registered based on deployment context:

| Profile   | Effect                                              |
| --------- | --------------------------------------------------- |
| `remote`  | Disables server-local filesystem/shell/cron tools   |
| `local`   | Keeps only local-machine tools; disables network tools |
| *(none)*  | All tools registered (default)                      |

```bash
# Remote deployment — no filesystem or shell access
toolregistry-hub openapi --profile remote

# Local-only — no web search or fetch
toolregistry-hub mcp --profile local
```

## Error Handling

Standard HTTP status codes:

| Code  | Meaning                         |
| ----- | ------------------------------- |
| `200` | Success                         |
| `400` | Bad request / invalid parameters |
| `401` | Authentication failed           |
| `500` | Internal server error           |

Error responses return `{"detail": "Error description"}`.

## Troubleshooting

| Issue                      | Solution                                                            |
| -------------------------- | ------------------------------------------------------------------- |
| Dependency install fails   | Ensure Python 3.10+                                                 |
| Port already in use        | Use `--port` to pick another                                        |
| Search tools unavailable   | Set API keys — see [Environment Variables](../reference/environment.md) |
| Auth failing               | Check `API_BEARER_TOKEN` and request header                         |
| MCP client rejects nullable parameter schemas | Upgrade to `toolregistry>=0.11.2` — nullable fields now emit a simplified `anyOf` schema compatible with strict MCP validators |

## See Also

- **[Launch a Server](../get-started/server.md)** — install and run
- **[CLI Reference](../reference/cli.md)** — all command-line options
- **[API Endpoints](../reference/endpoints.md)** — full endpoint listing
- **[Docker Deployment](docker.md)** — containerized setup
- **[Environment Variables](../reference/environment.md)** — every env var in one place
