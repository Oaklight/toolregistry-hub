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

# Download tool configuration (jsDelivr CDN, recommended)
curl -o tools.jsonc https://cdn.jsdelivr.net/gh/Oaklight/toolregistry-hub@master/tools.jsonc.example
# Or from GitHub directly
# curl -o tools.jsonc https://raw.githubusercontent.com/Oaklight/toolregistry-hub/master/tools.jsonc.example
chmod 644 tools.jsonc  # Ensure readable by container user (appuser)

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

## Web Fetch Tool

The `fetch_content` tool returns a **structured dict** (not a plain string):

```json
{
  "content": "...",
  "url": "https://example.com",
  "strategy": "readability",
  "quality": "high",
  "content_type": "text/html",
  "cached": false,
  "elapsed_ms": 123,
  "metadata": {"readability_score": 174.3, "content_length": 12345}
}
```

### `strategy` parameter

Leave as `"auto"` (default) for normal use. Specify a strategy explicitly when retrying after `auto` returns low-quality content:

| Strategy | Description |
|---|---|
| `auto` | Recommended — tries fallbacks in order |
| `markdown` | Cloudflare content negotiation |
| `readability` | Local readability extraction |
| `soup` | Local BeautifulSoup fallback |
| `veilrender` | Remote headless browser (requires `VEILRENDER_ENDPOINT`) |
| `cdp` | Self-hosted Chrome DevTools Protocol (requires `CDP_ENDPOINT`) |
| `jina` | Jina Reader API (always available; optional `JINA_API_KEY` for higher rate limits) |

Available choices are narrowed at runtime — `veilrender` and `cdp` appear only when their endpoints are configured.

### Fallback chain

```
markdown → readability → soup → veilrender → cdp → jina → local_fallback
```

### VeilRender configuration

VeilRender is an optional remote headless browser service for rendering JS-heavy pages and SPAs. To enable it, set the following in your `.env`:

```
VEILRENDER_ENDPOINT=https://your-veilrender-instance
VEILRENDER_TOKEN=your_token_here  # optional
```

When configured, `veilrender` is automatically inserted into the fallback chain before `cdp`.

## License

MIT
