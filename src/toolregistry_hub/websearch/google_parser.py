"""
Universal Google Search Results Parser

This module provides a unified parser for Google search results from different API providers
(Bright Data, Scrapeless, etc.). It handles the variations in field naming and structure
while producing standardized SearchResult objects.

Usage:
    from google_parser import GoogleResultParser, BRIGHTDATA_CONFIG, SCRAPELESS_CONFIG

    # For Bright Data
    parser = GoogleResultParser(BRIGHTDATA_CONFIG)
    results = parser.parse(api_response)

    # For Scrapeless
    parser = GoogleResultParser(SCRAPELESS_CONFIG)
    results = parser.parse(api_response)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from .search_result import SearchResult


@dataclass
class GoogleAPIConfig:
    """Configuration for parsing Google search results from different API providers.

    This configuration defines how to extract data from different API response formats.
    Each provider may use different field names for the same concept.
    """

    # Required fields
    results_key: (
        str  # Key for organic results array (e.g., "organic", "organic_results")
    )
    url_keys: List[str]  # Possible keys for URL field (in priority order)
    description_keys: List[
        str
    ]  # Possible keys for description field (in priority order)

    # Optional fields
    position_key: Optional[str] = (
        None  # Key for result position/rank (e.g., "rank", "position")
    )
    use_position_scoring: bool = False  # Whether to calculate score based on position


# Predefined configurations for known providers

BRIGHTDATA_CONFIG = GoogleAPIConfig(
    results_key="organic",
    url_keys=["link", "url"],
    description_keys=["description", "snippet"],
    position_key="rank",
    use_position_scoring=True,  # Use rank for scoring
)

SCRAPELESS_CONFIG = GoogleAPIConfig(
    results_key="organic_results",
    url_keys=["link", "redirect_link"],
    description_keys=["snippet", "description"],
    position_key="position",
    use_position_scoring=True,  # Use position for scoring
)


class GoogleResultParser:
    """Universal parser for Google search results from various API providers.

    This parser handles the differences in field naming and structure between
    different Google search API providers, producing standardized SearchResult objects.
    """

    def __init__(self, config: GoogleAPIConfig):
        """Initialize parser with provider-specific configuration.

        Args:
            config: Configuration defining how to parse this provider's response format
        """
        self.config = config

    def parse(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """Parse API response into standardized SearchResult objects.

        Args:
            response_data: Raw API response data (parsed JSON dict)

        Returns:
            List of standardized SearchResult objects
        """
        results = []

        # Extract organic results array
        organic_results = response_data.get(self.config.results_key, [])

        if not organic_results:
            logger.warning(
                f"No results found in response (key: '{self.config.results_key}')"
            )
            return results

        logger.debug(f"Parsing {len(organic_results)} organic results")

        for idx, item in enumerate(organic_results):
            try:
                result = self._parse_single_result(item, idx)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing result #{idx}: {e}")
                continue

        logger.debug(
            f"Successfully parsed {len(results)} results from {len(organic_results)} items"
        )
        return results

    def _parse_single_result(
        self, item: Dict[str, Any], index: int
    ) -> Optional[SearchResult]:
        """Parse a single search result item.

        Args:
            item: Single result item from API response
            index: Index of this item in the results array

        Returns:
            SearchResult object or None if parsing fails
        """
        # Extract URL (try multiple possible field names)
        url = self._extract_field(item, self.config.url_keys)
        if not url:
            logger.debug(
                f"Skipping result #{index} without URL: {item.get('title', 'No title')}"
            )
            return None

        # Extract description (try multiple possible field names)
        description = self._extract_field(item, self.config.description_keys)

        # Extract title
        title = item.get("title", "No title")

        # Calculate score
        score = self._calculate_score(item, index)

        return SearchResult(
            title=title,
            url=url,
            content=description or "No description available",
            score=score,
        )

    def _extract_field(
        self, item: Dict[str, Any], field_keys: List[str]
    ) -> Optional[str]:
        """Extract a field value trying multiple possible key names.

        Args:
            item: Data dict to extract from
            field_keys: List of possible key names (in priority order)

        Returns:
            First non-empty value found, or None
        """
        for key in field_keys:
            value = item.get(key)
            if value:
                return value
        return None

    def _calculate_score(self, item: Dict[str, Any], index: int) -> float:
        """Calculate relevance score for a search result.

        Args:
            item: Result item data
            index: Index in results array (0-based)

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not self.config.use_position_scoring or not self.config.position_key:
            return 1.0

        # Try to get position from item
        position = item.get(self.config.position_key)

        if position is None:
            # Fall back to index-based position (1-based)
            position = index + 1

        # Calculate score: higher position = lower score
        # Position 1 = 1.0, Position 2 = 0.95, Position 3 = 0.90, etc.
        score = 1.0 - (position * 0.05)

        # Clamp between 0.0 and 1.0
        return max(0.0, min(1.0, score))


def parse_brightdata_results(response_data: Dict[str, Any]) -> List[SearchResult]:
    """Convenience function to parse Bright Data Google search results.

    Args:
        response_data: Bright Data API response

    Returns:
        List of SearchResult objects
    """
    parser = GoogleResultParser(BRIGHTDATA_CONFIG)
    return parser.parse(response_data)


def parse_scrapeless_results(response_data: Dict[str, Any]) -> List[SearchResult]:
    """Convenience function to parse Scrapeless Google search results.

    Args:
        response_data: Scrapeless API response

    Returns:
        List of SearchResult objects
    """
    parser = GoogleResultParser(SCRAPELESS_CONFIG)
    return parser.parse(response_data)
