# Bright Data Google Search

This document describes how to use the Bright Data SERP API for Google searches.

## Overview

Bright Data is an enterprise-grade web data platform that provides powerful anti-bot bypass capabilities. By integrating Bright Data's SERP API, we can:

- ✅ Bypass Google's anti-bot mechanisms
- ✅ Get structured search results
- ✅ Support pagination
- ✅ No worries about IP bans or CAPTCHAs
- ✅ **Unified parsing** with other Google search providers

## Architecture

Bright Data search implementation uses a **universal Google result parser** ([`GoogleResultParser`](../../websearch/google_parser.md)) that:

- Handles variations in API response formats
- Provides consistent result scoring based on search position
- Simplifies maintenance and reduces code duplication
- Enables easy integration of new Google search providers

## Configuration

### 1. Get API Token

1. Visit [Bright Data](https://brightdata.com) and register an account
2. Create an API Token in the console
3. (Optional) Create or use an existing Web Unlocker Zone

### 2. Set Environment Variables

```bash
# Required: API Token
export BRIGHTDATA_API_KEY="your_api_token_here"

# Optional: Custom Zone (default is mcp_unlocker)
export BRIGHTDATA_ZONE="your_zone_name"
```

Or configure in `.env` file:

```env
BRIGHTDATA_API_KEY=your_api_token_here
BRIGHTDATA_ZONE=mcp_unlocker
```

## Usage

### Python API

```python
from toolregistry_hub.websearch import BrightDataSearch

# Initialize search client
search = BrightDataSearch()

# Basic search
results = search.search("python web scraping", max_results=10)

for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content[:200]}...")
    print(f"Score: {result.score}")  # Score based on search position
    print("-" * 50)

# Paginated search (get page 2 results)
results_page2 = search.search(
    "artificial intelligence",
    max_results=10,
    cursor="1"  # Page number starts from 0
)

# Custom timeout
results = search.search(
    "machine learning",
    max_results=5,
    timeout=30.0
)
```

### REST API

#### Endpoint

```
POST /web/search_brightdata_google
```

#### Request Example

```bash
curl -X POST "http://localhost:8000/web/search_brightdata_google" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_auth_token" \
  -d '{
    "query": "python web scraping",
    "max_results": 10,
    "timeout": 10.0,
    "cursor": "0"
  }'
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Search query string |
| `max_results` | integer | ❌ | 5 | Number of results to return (1-20) |
| `timeout` | float | ❌ | 10.0 | Request timeout in seconds |
| `cursor` | string | ❌ | "0" | Pagination cursor (page number, starts from 0) |

#### Response Example

```json
{
  "results": [
    {
      "title": "Python Web Scraping Tutorial",
      "url": "https://example.com/tutorial",
      "content": "Learn how to scrape websites using Python...",
      "score": 0.95
    },
    {
      "title": "Best Python Scraping Libraries",
      "url": "https://example.com/libraries",
      "content": "A comprehensive guide to Python scraping tools...",
      "score": 0.90
    }
  ]
}
```

**Note**: The `score` field now reflects the search result's position (higher position = higher score).

## Advanced Usage

### Batch Search

```python
from toolregistry_hub.websearch import BrightDataSearch

search = BrightDataSearch()

queries = ["python", "javascript", "golang"]
all_results = []

for query in queries:
    results = search.search(query, max_results=5)
    all_results.extend(results)

print(f"Total results retrieved: {len(all_results)}")
```

### Deep Search (Multiple Pages)

```python
from toolregistry_hub.websearch import BrightDataSearch

search = BrightDataSearch()

# Get first 50 results (automatic pagination)
results = search.search("machine learning", max_results=50)

# Or manually control pagination
all_results = []
for page in range(3):  # Get first 3 pages
    results = search.search(
        "deep learning",
        max_results=20,
        cursor=str(page)
    )
    all_results.extend(results)
```

### Custom Configuration

```python
from toolregistry_hub.websearch import BrightDataSearch

# Use custom configuration
search = BrightDataSearch(
    api_token="your_custom_token",
    zone="custom_zone_name",
    rate_limit_delay=2.0  # 2 seconds delay between requests
)

results = search.search("custom query")
```

## Result Scoring

Results are scored based on their position in search results:

- Position 1: score = 0.95
- Position 2: score = 0.90
- Position 3: score = 0.85
- And so on...

The scoring formula is: `score = 1.0 - (position * 0.05)`, clamped between 0.0 and 1.0.

This provides a more accurate representation of result relevance compared to a fixed score.

## Zone Explanation

**Zone** is a core concept in Bright Data, similar to a "proxy pool" or "service instance":

- Each Zone has independent quota and billing
- Default uses `mcp_unlocker` zone (Web Unlocker type)
- Can be customized via `BRIGHTDATA_ZONE` environment variable
- **Auto-creation**: If zone doesn't exist, the system will automatically create it (requires valid API key)

### Zone Auto-creation

When you initialize `BrightDataSearch`, the system will:

1. Check if the specified zone exists
2. If not, automatically create a Web Unlocker type zone
3. If creation fails, log a warning but continue running (zone may be created by Bright Data on first use)

You can also manually create a Zone:

1. Log in to [Bright Data Console](https://brightdata.com/cp)
2. Click the "Add" button
3. Select "Unlocker zone"
4. Enter zone name and create
5. Set the zone name in environment variables

## Error Handling

### Common Errors

#### 1. Authentication Failed (401)

```
Authentication failed. Check your BRIGHTDATA_API_KEY
```

**Solution**: Check if the API token is correctly set.

#### 2. Zone Not Found (422)

```
Zone 'your_zone' does not exist. Check your BRIGHTDATA_ZONE configuration
```

**Solution**: Create the zone in Bright Data console, or use the default `mcp_unlocker`.

#### 3. Rate Limit (429)

```
Rate limit exceeded, consider increasing rate_limit_delay
```

**Solution**: Increase the `rate_limit_delay` parameter value.

#### 4. Timeout Error

```
Bright Data API request timed out after 10s
```

**Solution**: Increase the `timeout` parameter value.

### Error Handling Example

```python
from toolregistry_hub.websearch import BrightDataSearch

try:
    search = BrightDataSearch()
    results = search.search("test query")
    
    if not results:
        print("No results found or error occurred")
    else:
        for result in results:
            print(f"{result.title} (score: {result.score})")
            
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Search failed: {e}")
```

## Performance Optimization

### 1. Rate Limiting

```python
# Set longer delay to avoid rate limits
search = BrightDataSearch(rate_limit_delay=2.0)
```

### 2. Timeout Settings

```python
# For complex queries, increase timeout
results = search.search("complex query", timeout=30.0)
```

### 3. Batch Processing

```python
# Get more results at once to reduce API calls
results = search.search("query", max_results=20)
```

## Limitations

- Maximum 20 results per request
- Maximum 180 results total (via pagination)
- Subject to Bright Data account quota limits
- Only supports Google search (no Bing, Yandex)

## Testing

Run tests:

```bash
# Run all Bright Data tests
pytest tests/websearch/test_websearch_brightdata.py -v

# Run specific test
pytest tests/websearch/test_websearch_brightdata.py::TestBrightDataGoogleSearch::test_search_basic -v

# Run debug tests to see raw API responses
python tests/websearch/test_debug_google_apis.py
```

## Technical Details

### Universal Parser

Bright Data search uses the [`GoogleResultParser`](../../websearch/google_parser.md) with the following configuration:

```python
BRIGHTDATA_CONFIG = GoogleAPIConfig(
    results_key="organic",
    url_keys=["link", "url"],
    description_keys=["description", "snippet"],
    position_key="rank",
    use_position_scoring=True,
)
```

This configuration tells the parser:
- Where to find organic results in the API response
- Which fields to check for URLs (in priority order)
- Which fields to check for descriptions
- How to calculate relevance scores

## Related Resources

- [Bright Data Official Documentation](https://docs.brightdata.com/)
- [Bright Data API Reference](https://docs.brightdata.com/api-reference)
- [Bright Data Console](https://brightdata.com/cp)
- [Universal Google Parser Documentation](../../websearch/google_parser.md)

## License

This integration follows the project's MIT license. Using Bright Data services requires compliance with their terms of service.