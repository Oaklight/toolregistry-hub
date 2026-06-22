---
title: Server Mode
summary: Deploy ToolRegistry Hub tools as REST API or MCP endpoints
description: Launch an OpenAPI or MCP server that exposes all hub tools as remote-callable endpoints.
keywords: server, openapi, mcp, rest api, deployment, fastapi
author: Oaklight
---

# Server Mode

ToolRegistry Hub can expose every tool as a network endpoint — either an OpenAPI (REST) server or an MCP server. Both modes auto-register all available tools; you just pick the protocol and start.

## Installation

```bash
# Full server (OpenAPI + MCP, Python 3.10+)
pip install toolregistry-hub[server]

# OpenAPI only
pip install toolregistry-hub[server_openapi]

# MCP only (Python 3.10+)
pip install toolregistry-hub[server_mcp]
```

## Start the Server

### OpenAPI

```bash
toolregistry-hub openapi --host 0.0.0.0 --port 8000
```

After startup:

- API root: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

### MCP

```bash
# Streamable HTTP (recommended for remote clients)
toolregistry-hub mcp --transport streamable-http --host 0.0.0.0 --port 8000

# SSE transport
toolregistry-hub mcp --transport sse --host 0.0.0.0 --port 8000

# Stdio transport (for local agent integration)
toolregistry-hub mcp --transport stdio
```

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

## Tool Configuration

Control which tools are loaded with a `tools.jsonc` file:

```bash
# Auto-discovered from working directory
cp tools.jsonc.example tools.jsonc

# Or specify via CLI
toolregistry-hub openapi --config path/to/tools.jsonc
```

### Denylist Mode (Default)

```jsonc
{
  "mode": "denylist",
  "disabled": ["file_ops"]  // disable specific tools
}
```

### Allowlist Mode

```jsonc
{
  "mode": "allowlist",
  "enabled": ["calculator", "datetime", "unit_converter"]
}
```

### Custom Tool Registration

```jsonc
{
  "tools": [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "my_package.MyTool", "namespace": "my_tool"}
  ]
}
```

## Calling the API

### curl

```bash
curl -X POST "http://localhost:8000/tools/calculator/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"expression": "2 + 2 * 3"}'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/tools/calculator/evaluate",
    json={"expression": "2 + 2 * 3"}
)
print(response.json())
```

## Error Handling

Standard HTTP status codes:

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request / invalid parameters |
| `401` | Authentication failed |
| `500` | Internal server error |

Error responses return `{"detail": "Error description"}`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dependency install fails | Ensure Python 3.10+ |
| Port already in use | Use `--port` to pick another |
| Search tools unavailable | Set API keys — see [Environment Variables](../reference/environment.md) |
| Auth failing | Check `API_BEARER_TOKEN` and request header |
| MCP client rejects nullable parameter schemas | Upgrade to `toolregistry>=0.11.2` — nullable fields now emit a simplified `anyOf` schema compatible with strict MCP validators |

## See Also

- **[CLI Reference](../reference/cli.md)** — all command-line options
- **[API Endpoints](../reference/endpoints.md)** — full endpoint listing
- **[Docker Deployment](docker.md)** — containerized setup
- **[Environment Variables](../reference/environment.md)** — every env var in one place
