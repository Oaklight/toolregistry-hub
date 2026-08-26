---
description: RedditSearch searches Reddit posts via the Arctic Shift API, a free archive of all public Reddit data from 2005 to present. Keyless, works out of the box.
keywords: reddit, arctic shift, search, subreddit, posts
---

# Reddit Search (Arctic Shift)

Reddit search provides functionality to search Reddit posts via the [Arctic Shift API](https://arctic-shift.photon-reddit.com/api/docs), a free archive of all public Reddit data from 2005 to present.

## Class Overview

- `RedditSearch` - A class that provides Reddit post search functionality

## Detailed API

### RedditSearch Class

`RedditSearch` is a class that provides Reddit post search functionality, inheriting from `BaseSearch`.

#### Initialization Parameters

- `base_url: str | None = None` - Arctic Shift API base URL, defaults to `ARCTIC_SHIFT_URL` environment variable, then the public instance

#### Methods

- `search(query: str, max_results: int = 5, timeout: float = 10.0, **kwargs) -> list[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> list[SearchResult]`: Implement specific search logic
- `_parse_results(raw_results: dict) -> list[SearchResult]`: Parse raw search results

### Subreddit Scoping

The Arctic Shift API requires a `subreddit` or `author` parameter for keyword searches — global full-text search is not supported. The engine parses subreddit references from the query string automatically:

- `r/python web scraping` — searches r/python for "web scraping"
- `/r/python web scraping` — same as above
- `subreddit:python web scraping` — explicit qualifier syntax

Alternatively, pass `subreddit="python"` as a keyword argument.

### Additional Parameters

The following Arctic Shift API parameters can be passed via `**kwargs`:

| Parameter | Description |
|-----------|-------------|
| `subreddit` | Subreddit name (overrides query-parsed value) |
| `author` | Filter by post author |
| `after` | Posts after this date (supports relative formats like `7d`) |
| `before` | Posts before this date |
| `sort` | Sort direction (`asc` or `desc`) |
| `over_18` | Filter NSFW content |
| `spoiler` | Filter spoiler-tagged posts |

## Free Tier

Arctic Shift is completely free:

- **No API key required** — works out of the box
- **No OAuth** — no Reddit account needed
- **No rate limit hassle** — dynamic limits, "a couple requests/sec" is safe
- **Full archive** — all public Reddit data from 2005 to present

!!! note "Data Freshness"
    Scores and comment counts may be unreliable for content less than 36 hours old.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ARCTIC_SHIFT_URL` | No | Override the Arctic Shift API base URL (for self-hosted instances) |

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import RedditSearch

search = RedditSearch()

# Search with subreddit in query
results = search.search("r/python web scraping", max_results=5)

for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Using Keyword Arguments

```python
from toolregistry_hub.websearch import RedditSearch

search = RedditSearch()

# Pass subreddit explicitly
results = search.search("web scraping", subreddit="python", max_results=5)

# Search by author
results = search.search("tutorial", author="spez")

# Filter by date range
results = search.search("r/python async", after="30d", before="1d")
```

### Via Unified Search

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()
results = ws.search("r/python web scraping", engine="reddit", count=5)
```
