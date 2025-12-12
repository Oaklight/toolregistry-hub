# ToolRegistry Hub Server

[![Docker Image Version](https://img.shields.io/docker/v/oaklight/toolregistry-hub-server?label=Docker&logo=docker)](https://hub.docker.com/r/oaklight/toolregistry-hub-server)
[![GitHub](https://img.shields.io/badge/GitHub-Oaklight/toolregistry--hub-blue?logo=github)](https://github.com/Oaklight/toolregistry-hub)
[![Docs](https://img.shields.io/badge/Docs-ReadTheDocs-blue?logo=readthedocs)](https://toolregistry-hub.readthedocs.io/en/latest/)

[Documentation](https://toolregistry-hub.readthedocs.io/en/latest/) | [中文文档](https://toolregistry-hub.readthedocs.io/zh-cn/latest/) | [GitHub](https://github.com/Oaklight/toolregistry-hub)

ToolRegistry Hub Server supports **MCP (Model Context Protocol)** and **OpenAPI** modes. It **replaces** [oaklight/openwebui-tool-server](https://github.com/Oaklight/openwebui-tool-server).

## Key Features

- Calculator, Datetime, Web Search (Brave/SearXNG/Tavily/Google), File Ops, Think, Todo, Web Fetch, etc.
- Full list: [docs](https://toolregistry-hub.readthedocs.io/en/latest/).

## Quick Docker Commands

**OpenAPI Mode (default):**

```
docker run -d --name toolregistry-hub -p 8000:8000 \
  -e API_BEARER_TOKEN=your_token_here \
  oaklight/toolregistry-hub-server:latest
```

Access: http://localhost:8000/docs

**MCP Streamable HTTP:**

```
docker run -d --name toolregistry-hub-mcp -p 8001:8000 \
  -e API_BEARER_TOKEN=your_token_here \
  oaklight/toolregistry-hub-server:latest \
  toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp
```

**MCP SSE:**

```
docker run -d --name toolregistry-hub-sse -p 8002:8000 \
  -e API_BEARER_TOKEN=your_token_here \
  oaklight/toolregistry-hub-server:latest \
  toolregistry-server --host=0.0.0.0 --port=8000 --mode=mcp --mcp-transport=sse
```

Replace `your_token_here` with token from [tokens.txt.example](tokens.txt.example). More envs in [.env.sample](.env.sample).

## Docker Compose (All Modes)

```
cp .env.sample .env  # Edit API keys
docker compose up -d
```

- OpenAPI: localhost:55093/docs
- MCP HTTP: localhost:55094
- MCP SSE: localhost:55095

Dev build: `docker compose -f compose.dev.yaml up`

## Build from Source

```
git clone https://github.com/Oaklight/toolregistry-hub
cd docker
docker build -t toolregistry-hub .
docker run -p 8000:8000 --env-file .env toolregistry-hub
```

## License

MIT
