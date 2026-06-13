---
title: Unified Web Search
summary: Single entry point for all web search providers with auto-selection and fallback
description: WebSearch wraps all available search providers behind a single search() method with engine selector, auto mode with priority chain, and per-instance dynamic annotation narrowing for LLM clients.
keywords: web search, unified search, auto select, engine selector, fallback, multi-provider
author: Oaklight
---

# Unified Web Search

The `WebSearch` class provides a single entry point that dispatches queries to any configured search provider. Instead of choosing a specific provider up front, you can let the wrapper auto-select the best available engine or pin a specific one with graceful fallback.

???+ note "Changelog"
    Unreleased — Added unified WebSearch entry point ([#88](https://github.com/Oaklight/toolregistry-hub/pull/88))  
    Unreleased — Parallel multi-engine search with BM25 dedup ([#142](https://github.com/Oaklight/toolregistry-hub/pull/142))  
    Unreleased — URL normalization for deduplication ([#143](https://github.com/Oaklight/toolregistry-hub/pull/143))

## Overview

- **Auto Mode**: `engine="auto"` tries configured providers in priority order, returning the first successful result
- **Parallel Mode**: `engine="parallel"` queries multiple engines concurrently, deduplicates by URL, and re-ranks results with BM25 scoring for higher quality
- **Specific Engine**: Pin `engine="brave"` (or any other provider) for deterministic routing
- **Fallback**: Set `fallback=True` so a failed specific engine falls through to the auto chain
- **Dynamic Schema**: The `engine` parameter’s accepted values are narrowed at runtime to only the engines with valid API keys, so LLM clients see an accurate JSON schema
- **Configurable Priority**: Override the default engine order via `WEBSEARCH_PRIORITY` environment variable

## Quick Start

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()

# Auto-select the best configured provider
results = ws.search("Python 3.13 new features", count=5)

# Parallel mode: query multiple engines, deduplicate and re-rank
results = ws.search("machine learning", engine="parallel", count=10)

# Use a specific engine
results = ws.search("machine learning", engine="tavily")

# Specific engine with fallback to auto chain
results = ws.search("quantum computing", engine="brave", fallback=True)

# Check which engines are available
print(ws.list_engines())
# {'brave': True, 'tavily': True, 'searxng': False, ...}
```

## API Reference

### `WebSearch(priority)`

Initialize the unified search wrapper.

**Parameters:**

- `priority` (str, optional): Comma-separated engine names for priority order. Falls back to `WEBSEARCH_PRIORITY` environment variable, then the default order.

### `WebSearch.search(query, *, count, engine, fallback, timeout)`

Perform a web search via the selected engine.

**Parameters:**

- `query` (str): The search query string
- `count` (int): Number of results to return (default 5, max 20)
- `engine` (str): Provider to use. `"auto"` (default) tries configured engines in priority order. `"parallel"` queries multiple engines concurrently and deduplicates with BM25 re-ranking. Specific values: `"brave"`, `"tavily"`, `"searxng"`, `"brightdata"`, `"scrapeless"`, `"serper"`
- `fallback` (bool): If `True` and the chosen engine fails, automatically try the next available engine instead of raising an error. Default: `False`
- `timeout` (float): Per-request timeout in seconds. Default: 10.0

**Returns:** `list[SearchResult]` — each with `title`, `url`, `content`, and `score`

**Raises:**

- `ValueError`: Unknown engine name or empty query
- `RuntimeError`: No engine available (auto mode), or requested engine unavailable with `fallback=False`

### `WebSearch.list_engines()`

List all known engines and their configuration status.

**Returns:** `dict[str, bool]` - mapping of engine name to configured status

## Engine Priority

The default priority order (paid/higher-quality first):

1. `tavily`
2. `brave`
3. `serper`
4. `brightdata`
5. `scrapeless`
6. `searxng`

Override via environment variable:

```bash
export WEBSEARCH_PRIORITY="searxng,brave,tavily"
```

Or at construction time:

```python
ws = WebSearch(priority="searxng,brave")
```

## Auto Mode Behavior

When `engine="auto"`:

1. Engines are tried in priority order
2. Unconfigured engines (missing API keys) are skipped
3. If an engine returns empty results, the next engine is tried
4. If an engine raises an exception, the next engine is tried
5. If all engines fail, a `RuntimeError` is raised with the last error

## Parallel Mode

When `engine="parallel"`:

1. All engines listed in `WEBSEARCH_PARALLEL_ENGINES` are queried concurrently via `ThreadPoolExecutor`
2. Unconfigured engines are skipped; individual engine failures are logged but don't abort the search
3. Results are deduplicated by normalized URL (strips `www.` prefix, trailing slashes, and tracking parameters like `utm_*`, `fbclid`, `gclid`)
4. When duplicate URLs are found, the result with the longest content is kept
5. Remaining results are re-ranked using BM25 scoring against the original query
6. If all parallel engines return empty or fail, falls back to auto mode

Configure which engines to use in parallel:

```bash
# Default: brightdata,brave
export WEBSEARCH_PARALLEL_ENGINES="brightdata,brave,tavily"
```

## Fallback Behavior

When a specific engine is requested with `fallback=True`:

```python
# If brave is down, automatically try other engines
results = ws.search("query", engine="brave", fallback=True)
```

The failed engine is excluded from the fallback auto chain to avoid retrying it.

## Dynamic Annotation Narrowing

At construction time, `WebSearch` probes which engines are configured and dynamically narrows the `engine` parameter's type annotation. This means:

- **IDE autocomplete** shows only the full menu (all engines)
- **LLM JSON schema** (generated at runtime) shows only configured engines
- **Different instances** can have different available engines

```python
# Server has BRAVE_API_KEY and TAVILY_API_KEY set
ws = WebSearch()
# LLM client sees: engine: Literal["auto", "brave", "tavily"]
# Not the full 7-engine menu
```

## Server Mode

In server mode, `WebSearch` is registered at the `web/websearch` namespace. The 6 individual provider tools are marked as deferred - discoverable via `discover_tools` but not included in the initial schema. This reduces schema size while keeping all providers accessible.

```
POST /tools/web/websearch/search
POST /tools/web/websearch/list_engines
```
