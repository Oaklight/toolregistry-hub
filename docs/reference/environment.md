---
title: Environment Variables
summary: All environment variables used by ToolRegistry Hub
description: Complete reference for authentication, tool API keys, and server configuration environment variables.
keywords: environment, variables, api keys, configuration, auth
author: Oaklight
---

# Environment Variables

## Authentication

| Variable | Description |
|----------|-------------|
| `API_BEARER_TOKEN` | Bearer token(s) for API auth. Single token or comma-separated list. |
| `API_BEARER_TOKENS_FILE` | Path to a file containing tokens, one per line. |

If neither is set, the server runs without authentication.

## Tool API Keys

| Variable | Tool | Description |
|----------|------|-------------|
| `BRAVE_API_KEY` | Brave Search | Brave Search API key ([get one](https://api.search.brave.com/)) |
| `TAVILY_API_KEY` | Tavily Search | Tavily API key ([get one](https://tavily.com/)) |
| `SERPER_API_KEY` | Serper Search | Serper API key ([get one](https://serper.dev/)) |
| `BRIGHTDATA_API_KEY` | BrightData Search | Bright Data API key ([get one](https://brightdata.com/)) |
| `SCRAPELESS_API_KEY` | Scrapeless Search | Scrapeless API key ([get one](https://scrapeless.com/)) |
| `SEARXNG_URL` | SearXNG Search | SearXNG instance URL (e.g., `http://localhost:8080`) |
| `SEARXNG_API_KEY` | SearXNG Search | Optional API key for protected instances (sent as `X-API-Key` header) |
| `JINA_API_KEY` | Fetch (Jina Reader) | Optional; comma-separated for multi-key rotation |
| `CDP_ENDPOINT` | Fetch (CDP Rendering) | Optional WebSocket URL of a CDP-compatible browser (e.g., `ws://localhost:9222`) |

## Server Configuration

| Variable | Description |
|----------|-------------|
| `WEBSEARCH_PRIORITY` | Comma-separated engine priority for auto mode (e.g., `searxng,brave,tavily`) |
| `TOOLS_CONFIG` | Path to a `tools.jsonc` configuration file (alternative to `--config` CLI flag) |

## Auto-Disable Behavior

When the server starts, it checks each tool's required environment variables. Tools with missing variables are registered but disabled — they won't appear in the tool list returned to clients. Set the required variables and restart to enable them.

## Using `.env` Files

The server loads `.env` from the current directory by default. Override with:

```bash
toolregistry-hub openapi --env /path/to/.env
toolregistry-hub openapi --no-env  # skip .env loading entirely
```
