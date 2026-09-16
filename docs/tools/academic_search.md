---
title: Academic Search
summary: Search academic papers via OpenAlex and arXiv
---

# Academic Search

The `academics` namespace provides academic paper search across multiple engines.

## Engines

| Engine | Source | Auth Required | Free Tier |
|--------|--------|---------------|-----------|
| OpenAlex | [openalex.org](https://openalex.org/) | No | Unlimited (polite pool) |
| arXiv | [arxiv.org](https://arxiv.org/) | No | Unlimited |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENALEX_MAILTO` | Email for OpenAlex polite pool (higher rate limits, recommended) |
| `ACADEMIC_SEARCH_PRIORITY` | Comma-separated engine priority (default: `openalex,arxiv`) |

## Usage

```python
from toolregistry_hub.academics import AcademicSearch

search = AcademicSearch()
results = search.search("transformer attention mechanism", engine="openalex", count=5)
for r in results:
    print(f"{r.title} — {r.url}")
```

### API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tools/academics/search` | Search academic papers |
| POST | `/tools/academics/list_engines` | List available academic search engines |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query |
| `engine` | string | `"auto"` | Engine to use: `auto`, `openalex`, `arxiv` |
| `count` | integer | `5` | Number of results (max 20) |

### Result Fields

Each result includes: `title`, `authors`, `abstract`, `url`, `year`, `venue`, `doi`, `pdf_url`, `cited_by_count`, `source`.
