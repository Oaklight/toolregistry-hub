---
description: GitHubSearch searches GitHub repositories via the GitHub REST Search API. Works unauthenticated out of the box, with optional PAT-based authentication for higher rate limits.
keywords: github, search, repositories, api, stars, language, topics
---

# GitHub Search

GitHub search provides functionality to search GitHub repositories via the [GitHub REST Search API](https://docs.github.com/en/rest/search/search#search-repositories).

## Class Overview

- `GitHubSearch` - A class that provides GitHub repository search functionality

## Detailed API

### GitHubSearch Class

`GitHubSearch` inherits from `BaseSearch` and provides GitHub repository search with optional PAT-based authentication and key rotation.

#### Initialization Parameters

- `api_keys: str | None = None` - Comma-separated GitHub personal access tokens. Falls back to `GITHUB_TOKENS` env var, then unauthenticated access
- `rate_limit_delay: float = 1.0` - Delay between requests in seconds

#### Methods

- `search(query: str, max_results: int = 5, timeout: float = 10.0, **kwargs) -> list[SearchResult]`: Execute search and return results
- `_search_impl(query: str, **kwargs) -> list[SearchResult]`: Implement specific search logic with key rotation
- `_parse_results(raw_results: dict) -> list[SearchResult]`: Parse raw search results

### Query Syntax

The query string is passed directly to the GitHub Search API, so you can use [GitHub search qualifiers](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories):

- `machine learning language:python` — Python repos about machine learning
- `web framework stars:>1000` — popular web frameworks
- `topic:deep-learning language:python` — repos tagged with deep-learning
- `org:google language:go` — Go repos from Google

### Additional Parameters

The following parameters can be passed via `**kwargs`:

| Parameter | Description |
|-----------|-------------|
| `sort` | Sort field: `stars`, `forks`, `help-wanted-issues`, `updated` |
| `order` | Sort order: `desc` (default) or `asc` |
| `page` | Page number for pagination |

## Free Tier

GitHub Search API works without any authentication:

- **No API key required** — works out of the box
- **Unauthenticated**: 10 search requests/minute
- **Authenticated** (with PATs): 30 search requests/minute per token
- **Key rotation**: distribute load across multiple PATs for higher aggregate throughput

!!! note "Domain-Specific Engine"
    GitHub search is a domain-specific engine that searches repositories, not general web content. It is not included in the `"auto"` or `"parallel"` engine chains — select it explicitly via `engine="github"`.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKENS` | No | Comma-separated GitHub personal access tokens for higher rate limits |

## Usage Examples

### Basic Usage

```python
from toolregistry_hub.websearch import GitHubSearch

search = GitHubSearch()

# Search with GitHub qualifiers
results = search.search("machine learning language:python stars:>1000", max_results=5)

for result in results:
    print(f"Repo: {result.title}")
    print(f"URL: {result.url}")
    print(f"Info: {result.content}")
    print("-" * 50)
```

### Sorted by Stars

```python
from toolregistry_hub.websearch import GitHubSearch

search = GitHubSearch()

# Find most-starred Python web frameworks
results = search.search(
    "web framework language:python",
    max_results=10,
    sort="stars",
    order="desc",
)
```

### With Authentication

```python
import os
os.environ["GITHUB_TOKENS"] = "ghp_token1,ghp_token2"

from toolregistry_hub.websearch import GitHubSearch

search = GitHubSearch()
# Automatically uses PATs with key rotation
results = search.search("topic:machine-learning stars:>5000")
```

### Via Unified Search

```python
from toolregistry_hub.websearch import WebSearch

ws = WebSearch()
results = ws.search("machine learning language:python", engine="github", count=5)
```
