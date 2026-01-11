from .search_result import SearchResult
from .websearch_bing import BingSearch  # Deprecated: use alternatives instead
from .websearch_brave import BraveSearch
from .websearch_brightdata import BrightDataSearch
from .websearch_gemini import GeminiSearch
from .websearch_scrapeless import ScrapelessSearch
from .websearch_searxng import SearXNGSearch
from .websearch_tavily import TavilySearch

__all__ = [
    "BingSearch",  # Deprecated: frequent bot detection issues
    "BraveSearch",
    "BrightDataSearch",
    "GeminiSearch",
    "ScrapelessSearch",
    "SearchResult",
    "SearXNGSearch",
    "TavilySearch",
]
