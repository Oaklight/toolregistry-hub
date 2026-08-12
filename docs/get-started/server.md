---
title: Launch a Server
summary: Start a ToolRegistry Hub server and send your first request
description: Get an OpenAPI or MCP server running in under a minute, then call a tool endpoint.
keywords: server, quickstart, openapi, mcp, first request
author: Oaklight
---

# Launch a Server

ToolRegistry Hub can expose every tool as a network endpoint — either an OpenAPI (REST) server or an MCP server. This page walks you from install to first request.

## Install server dependencies

```bash
# Full server (OpenAPI + MCP, Python 3.10+)
pip install toolregistry-hub[server]

# OpenAPI only
pip install toolregistry-hub[server_openapi]

# MCP only (Python 3.10+)
pip install toolregistry-hub[server_mcp]
```

## Start the server

### OpenAPI

```bash
toolregistry-hub openapi --host 0.0.0.0 --port 8000
```

Once running:

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

## Send your first request

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
    json={"expression": "2 + 2 * 3"},
)
print(response.json())  # {"result": "8"}
```

## Next steps

| I want to…                              | Go to                                                  |
| ---------------------------------------- | ------------------------------------------------------ |
| Configure auth or tool loading           | [Server Configuration](../guides/server.md)            |
| Run with Docker                          | [Docker Deployment](../guides/docker.md)               |
| See all CLI flags                        | [CLI Reference](../reference/cli.md)                   |
| Browse every endpoint                    | [API Endpoints](../reference/endpoints.md)             |
| Use tools as a Python library instead    | [Library Usage](../guides/library.md)                  |
