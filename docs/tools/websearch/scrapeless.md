# Scrapeless Google Search

Scrapeless Google Search provides functionality to perform Google web searches using the Scrapeless DeepSERP API. Scrapeless offers powerful web scraping capabilities with built-in anti-bot bypass and returns structured, pre-parsed search results without requiring HTML parsing.

## Overview

- **Provider**: Scrapeless DeepSERP API
- **Search Engine**: Google only
- **Architecture**: Uses universal [`GoogleResultParser`](../../websearch/google_parser.md)
- **Scoring**: Position-based relevance scoring

## Class Overview

- `ScrapelessSearch` - A class that provides Scrapeless DeepSERP API Google search functionality

#### Initialization Parameters

- `api_keys: Optional[str] = None` - Comma-separated Scrapeless API keys. If not provided, will try to get from SCRAPELESS_API_KEY env var
- `base_url: Optional[str] = "https://api.scrapeless.com"` - Base URL for Scrapeless API

## Architecture

Scrapeless search implementation uses a **universal Google result parser** ([`GoogleResultParser`](../../websearch/google_parser.md)) that:

- Handles variations in API response formats
- Provides consistent result scoring based on search position
- Simplifies maintenance and reduces code duplication
- Enables easy integration of new Google search providers

## Setup

1. Sign up at <https://app.scrapeless.com/> to get an API key
2. Set your API key as an environment variable:

   ```bash
   export SCRAPELESS_API_KEY="your-scrapeless-api-key-here"
   ```

## Usage Examples

### Basic Google Search

```python
from toolregistry_hub.websearch import ScrapelessSearch

# Create Scrapeless search instance
scrapeless_search = ScrapelessSearch()

# Execute Google search
results = scrapeless_search.search("Python programming", max_results=5)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")  # Position-based score
    print("-" * 50)
```

### Using Multiple API Keys

```python
from toolregistry_hub.websearch import ScrapelessSearch

# Create search instance with multiple API keys for load balancing
api_keys = "key1,key2,key3"
scrapeless_search = ScrapelessSearch(api_keys=api_keys)

# Execute search
results = scrapeless_search.search("machine learning tutorial", max_results=10)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content}")
    print("-" * 50)
```

### Search with Language and Country Parameters

```python
from toolregistry_hub.websearch import ScrapelessSearch

# Create search instance
scrapeless_search = ScrapelessSearch()

# Search in English from US
us_results = scrapeless_search.search(
    "artificial intelligence",
    max_results=10,
    language="en",
    country="us"
)

# Search in Chinese from China
cn_results = scrapeless_search.search(
    "人工智能",
    max_results=10,
    language="zh-CN",
    country="cn"
)

# Search in Spanish from Spain
es_results = scrapeless_search.search(
    "inteligencia artificial",
    max_results=10,
    language="es",
    country="es"
)

# Process results
for result in us_results:
    print(f"US Result: {result.title} (score: {result.score})")
    print(f"URL: {result.url}")
    print("-" * 50)
```

### Custom API Configuration

```python
from toolregistry_hub.websearch import ScrapelessSearch

# Create search instance with custom configuration
scrapeless_search = ScrapelessSearch(
    api_keys="your-api-key-here",
    base_url="https://api.scrapeless.com"
)

# Execute search with custom timeout
results = scrapeless_search.search(
    "deep learning frameworks",
    max_results=15,
    timeout=30.0,
    language="en",
    country="us"
)

# Process search results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Content: {result.content[:150]}...")
    print(f"Score: {result.score}")
    print("-" * 50)
```

### Multi-Region Search Comparison

```python
from toolregistry_hub.websearch import ScrapelessSearch

# Create search instance
scrapeless_search = ScrapelessSearch()

query = "climate change"
regions = [
    ("en", "us"),
    ("en", "uk"),
    ("zh-CN", "cn"),
    ("ja", "jp")
]

# Search across multiple regions
all_results = {}
for language, country in regions:
    results = scrapeless_search.search(
        query,
        max_results=5,
        language=language,
        country=country
    )
    all_results[f"{language}_{country}"] = results
    print(f"\n=== {language.upper()} / {country.upper()} Results ===")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title} (score: {result.score})")
        print(f"   {result.url}")
```

## API Parameters

The Scrapeless Google Search supports the following parameters:

- `query`: Search query string (required)
- `max_results`: Maximum number of results to return (default: 5, recommended: 1-20)
- `timeout`: Request timeout in seconds (default: 10.0)
- `language`: Language code for search results (default: "en")
  - Examples: "en", "zh-CN", "es", "fr", "de", "ja", "ko"
- `country`: Country code for search localization (default: "us")
  - Examples: "us", "uk", "cn", "jp", "de", "fr", "es"

## Result Scoring

Results are scored based on their position in search results:

- Position 1: score = 0.95
- Position 2: score = 0.90
- Position 3: score = 0.85
- And so on...

The scoring formula is: `score = 1.0 - (position * 0.05)`, clamped between 0.0 and 1.0.

This provides an accurate representation of result relevance based on Google's ranking.

## Features

- **Google Search Only**: Specialized for Google search via DeepSERP API
- **Structured Results**: Returns pre-parsed, structured data without HTML parsing
- **Anti-Bot Bypass**: Built-in capabilities to bypass anti-scraping measures
- **Language Support**: Search in multiple languages with proper localization
- **Country Targeting**: Get region-specific search results
- **Error Handling**: Comprehensive error handling and logging
- **Timeout Control**: Configurable request timeouts
- **Easy Integration**: Simple API compatible with other search providers
- **Universal Parser**: Uses shared parsing logic for consistency

## Technical Details

### How It Works

Scrapeless Google Search uses the DeepSERP API (`scraper.google.search`) which:

1. Sends your search query with language and country parameters
2. Executes the search on Google's servers
3. Bypasses anti-bot protection mechanisms
4. Returns structured, pre-parsed search results
5. No HTML parsing required on your end

### Request Payload

The tool sends requests to Scrapeless API with the following structure:

```json
{
  "actor": "scraper.google.search",
  "input": {
    "q": "your search query",
    "hl": "en",
    "gl": "us"
  },
  "async": false
}
```

### Response Format

The DeepSERP API returns structured data:

```json
{
  "organic_results": [
    {
      "position": 1,
      "title": "Result Title",
      "link": "https://example.com",
      "snippet": "Result description...",
      "redirect_link": "https://...",
      "snippet_highlighted_words": ["keyword1", "keyword2"],
      "source": "example.com"
    }
  ]
}
```

### Universal Parser Configuration

Scrapeless search uses the [`GoogleResultParser`](../../websearch/google_parser.md) with the following configuration:

```python
SCRAPELESS_CONFIG = GoogleAPIConfig(
    results_key="organic_results",
    url_keys=["link", "redirect_link"],
    description_keys=["snippet", "description"],
    position_key="position",
    use_position_scoring=True,
)
```

This configuration tells the parser:

- Where to find organic results (`organic_results` array)
- Which fields to check for URLs (tries `link` first, then `redirect_link`)
- Which fields to check for descriptions (tries `snippet` first, then `description`)
- How to calculate relevance scores (based on `position` field)

## Error Handling

The tool handles various error scenarios:

- **401 Unauthorized**: Invalid API key
- **429 Rate Limit**: Too many requests
- **Timeout**: Request exceeded timeout limit
- **JSON Parse Errors**: Malformed API response

All errors are logged and return an empty result list.

## Best Practices

1. **API Key Security**: Store your API key in environment variables, not in code
2. **Rate Limiting**: Be mindful of API rate limits and usage quotas
3. **Timeout Settings**: Adjust timeout based on your network conditions
4. **Result Limits**: Use reasonable `max_results` values (1-20 recommended)
5. **Language/Country**: Choose appropriate language and country codes for your use case
6. **Error Handling**: Always check if results are empty before processing

## Limitations

- Maximum recommended results per query: 20
- Only supports Google search (not Bing, DuckDuckGo, etc.)
- API usage is subject to Scrapeless pricing and quotas
- Some queries may be restricted based on region or content

## Testing

Run tests:

```bash
# Run all Scrapeless tests
pytest tests/websearch/test_websearch_scrapeless.py -v

# Run specific test
pytest tests/websearch/test_websearch_scrapeless.py::TestScrapelessGoogleSearch::test_search_basic -v

# Run debug tests to see raw API responses
python tests/websearch/test_debug_google_apis.py
```

## Related Resources

- [Scrapeless API Documentation](https://docs.scrapeless.com/)
- [Universal Google Parser Documentation](../../websearch/google_parser.md)
- [Scrapeless Console](https://app.scrapeless.com/)

## API Documentation

For complete Scrapeless API documentation, refer to: <https://docs.scrapeless.com/>
