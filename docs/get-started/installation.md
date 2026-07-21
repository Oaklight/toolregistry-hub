---
title: Installation
summary: Install ToolRegistry Hub as a Python library or with server extras
description: Step-by-step installation for toolregistry-hub — library-only, server extras, or Docker.
keywords: install, pip, python, setup, server, docker
author: Oaklight
---

# Installation

## Library Only

```bash
pip install toolregistry-hub
```

This gives you every tool as a direct Python import — no server, no extra dependencies.

## With Server Extras

If you want to expose tools as REST API or MCP endpoints:

!!! tip
    **zsh users** (default on macOS): wrap the package name in quotes, e.g. `pip install 'toolregistry-hub[server]'` — zsh treats `[]` as glob patterns.

```bash
# Full server (OpenAPI + MCP, Python 3.10+)
pip install toolregistry-hub[server]

# OpenAPI server only
pip install toolregistry-hub[server_openapi]

# MCP server only (Python 3.10+)
pip install toolregistry-hub[server_mcp]
```

## Docker

Pre-built images are available on Docker Hub:

```bash
docker run -p 8000:8000 oaklight/toolregistry-hub-server:latest
```

See [Docker Deployment](../guides/docker.md) for compose files and production setup.

## Verify

```python
from toolregistry_hub import Calculator

print(Calculator.evaluate("1 + 1"))  # 2
```

## Next Steps

- **[Quick Start](quickstart.md)** — try tools in 60 seconds
- **[Library Usage](../guides/library.md)** — full library guide
- **[Server Mode](../guides/server.md)** — deploy as an API server
