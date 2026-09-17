---
name: toolregistry-hub
version: 0.10.0
description: "ToolRegistry Hub — remote tool server exposing calculator, datetime, unit conversion, web search, academic search, weather, web fetch, and more via OpenAPI REST endpoints. Supports tool discovery and deferred tool calling."
homepage: https://github.com/Oaklight/toolregistry-hub
metadata:
  {
    "openclaw":
      {
        "emoji": "🧰",
        "requires": { "bins": ["curl", "jq"] },
      },
  }
---

# ToolRegistry Hub — Remote Tool Server

Call tools hosted on a ToolRegistry Hub server via its OpenAPI REST endpoints.
Use this when you need calculator, web search, academic search, weather,
datetime, unit conversion, web fetch, or other registered tools via HTTP.

## Deploy with Docker

The fastest way to get a running instance. Multi-arch images (amd64 + arm64)
are published to DockerHub on every release.

### Standalone (single mode)

```bash
# OpenAPI mode (default)
docker run -d -p 8000:8000 \
  -e API_BEARER_TOKEN=changeme \
  oaklight/toolregistry-hub-server:latest

# MCP Streamable HTTP
docker run -d -p 8000:8000 \
  -e API_BEARER_TOKEN=changeme \
  oaklight/toolregistry-hub-server:latest \
  toolregistry-hub mcp --transport=streamable-http --host=0.0.0.0 --port=8000
```

### Full stack (OpenAPI + MCP + Caddy gateway)

```bash
# Grab the compose files
curl -LO https://raw.githubusercontent.com/Oaklight/toolregistry-hub/master/docker/compose.yaml
curl -LO https://raw.githubusercontent.com/Oaklight/toolregistry-hub/master/docker/Caddyfile

# Create .env
cat > .env << 'ENV'
API_BEARER_TOKEN=your-secret-token
GATEWAY_PORT=8080
IMAGE_TAG=latest
ENV

# Start
docker compose up -d
```

The Caddy gateway exposes everything on a single port:

| Path | Backend |
|------|---------|
| `/docs` | OpenAPI interactive docs |
| `/mcp` | MCP Streamable HTTP |
| `/sse` | MCP SSE |
| `/admin/openapi/` | Admin panel (basic auth) |
| `/admin/mcp-http/` | Admin panel (basic auth) |
| `/admin/mcp-sse/` | Admin panel (basic auth) |
| `/*` | OpenAPI endpoints |

For tool customization, optional env vars, and admin panel setup, see the
full [Docker Deployment Guide](https://toolregistry-hub.readthedocs.io/en/latest/guides/docker/).

Source code: <https://github.com/Oaklight/toolregistry-hub>

## Connect to a running instance

Config persisted in `~/.config/toolregistry-hub/config.json` (`0600`).

```bash
eval $(python3 -c "
import json, os, pathlib
cfg = {}
p = pathlib.Path.home() / '.config' / 'toolregistry-hub' / 'config.json'
if p.exists(): cfg = json.loads(p.read_text())
url = os.environ.get('TOOLREGISTRY_HUB_URL') or cfg.get('url', '')
token = os.environ.get('TOOLREGISTRY_HUB_TOKEN') or cfg.get('token', '')
print(f'export TOOLREGISTRY_HUB_URL=\"{url}\"')
print(f'export TOOLREGISTRY_HUB_TOKEN=\"{token}\"')
")
# Verify — should print tool count
curl -sf -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  "$TOOLREGISTRY_HUB_URL/tools" | jq '[.[] | .name] | length'
```

If URL is missing, ask the user for the server URL and bearer token.

Save config:
```bash
python3 -c "
import json, os, pathlib
d = pathlib.Path.home() / '.config' / 'toolregistry-hub'; d.mkdir(parents=True, exist_ok=True)
p = d / 'config.json'; p.write_text(json.dumps({'url': '$URL', 'token': '$TOKEN'}, indent=2))
os.chmod(p, 0o600); print(f'Saved to {p}')
"
```

## Calling tools

All tools use `POST /tools/<namespace>/<name>` with JSON body:

```bash
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/<namespace>/<name>" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"param1": "value1"}' | jq .
```

## Tool reference

### Calculator

```bash
# Evaluate expression
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/calculator/evaluate" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expression": "sqrt(144) + pi"}' | jq .

# List allowed functions
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/calculator/list_allowed_fns" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"with_help": false}' | jq .
```

### Date & Time

```bash
# Current time
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/datetime/now" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timezone_name": "Asia/Tokyo"}' | jq .

# Convert timezone
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/datetime/convert_timezone" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"time_str": "14:30", "source_timezone": "America/New_York", "target_timezone": "Asia/Shanghai"}' | jq .
```

### Unit Converter

```bash
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/unit_converter/convert" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 100, "conversion": "celsius_to_fahrenheit"}' | jq .
```

### Web Search

```bash
# Auto-select best engine
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/web/websearch/search" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "rust programming language", "count": 5}' | jq .

# Specific engine: brave, tavily, searxng, brightdata, scrapeless, serper, reddit, github
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/web/websearch/search" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "toolregistry", "engine": "github", "count": 3}' | jq .

# Reddit (requires r/<subreddit> in query)
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/web/websearch/search" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "r/LocalLLaMA tool calling", "engine": "reddit", "count": 3}' | jq .
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query |
| `engine` | string | `"auto"` | `auto`, `parallel`, or a specific engine name |
| `count` | integer | `5` | Number of results (max 20) |

### Academic Search

```bash
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/academics/search" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention mechanism", "engine": "openalex", "count": 3}' | jq .
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query |
| `engine` | string | `"auto"` | `auto`, `openalex`, `arxiv` |
| `count` | integer | `5` | Number of results (max 20) |

Results include: `title`, `authors`, `abstract`, `url`, `year`, `venue`, `doi`, `pdf_url`, `cited_by_count`, `source`.

### Weather

```bash
# Current conditions
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/weather/get_current" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"location": "Tokyo"}' | jq .

# Forecast (up to 3 days)
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/weather/get_forecast" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"location": "San Francisco", "days": 3}' | jq .

# Astronomy (sunrise, sunset, moon phase)
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/weather/get_astronomy" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"location": "London"}' | jq .
```

### Web Fetch

```bash
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/web/fetch/fetch_content" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "timeout": 30}' | jq .
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | URL to fetch |
| `timeout` | float | `30` | Timeout in seconds |
| `strategy` | string | `"auto"` | `auto`, `markdown`, `readability`, `soup`, `jina`, `veilrender` |

### Think Tool

```bash
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/think/think" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"thinking_mode": "reasoning", "focus_area": "architecture", "thought_process": "..."}' | jq .
```

### Tool Discovery & Deferred Calling

```bash
# Discover tools by keyword
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/default/discover_tools" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "calculator"}' | jq '.[].name'

# Call a deferred tool by name
curl -s -X POST "$TOOLREGISTRY_HUB_URL/tools/default/call_deferred" \
  -H "Authorization: Bearer $TOOLREGISTRY_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"_target_tool": "calculator-help", "fn_name": "sqrt"}' | jq .
```

## Error handling

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | — |
| 401 | Unauthorized | Check bearer token |
| 404 | Tool not found | Check tool name / namespace |
| 422 | Validation error | Check request parameters |
| 500 | Tool execution failed | See `detail` field for error message |
