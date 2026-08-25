from abc import ABC, abstractmethod
from typing import Any

from .._vendor.httpclient import HTTPError
from .._vendor.structlog import get_logger
from .paper_result import PaperResult

logger = get_logger()

TIMEOUT_DEFAULT = 10.0


class AcademicSearchBackendError(Exception):
    """Raised when an academic search backend returns an error instead of results."""


class BaseAcademicSearch(ABC):
    def _is_configured(self) -> bool:
        """Check if the search engine has valid configuration.

        Default implementation checks if ``api_key_parser`` has keys.
        Subclasses without API keys should override to return ``True``.
        """
        parser = getattr(self, "api_key_parser", None)
        if parser is not None:
            return bool(parser.api_keys)
        return True

    @abstractmethod
    def search(
        self, query: str, *, max_results: int = 5, timeout: float = 10.0, **kwargs
    ) -> list[PaperResult]:
        """Search for academic papers.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return (1-100).
            timeout: Request timeout in seconds.

        Returns:
            List of paper results.
        """

    @abstractmethod
    def _parse_results(self, raw_results: Any) -> list[PaperResult]:
        """Parse raw API response into PaperResult objects."""

    @abstractmethod
    def _search_impl(self, query: str, **kwargs) -> list[PaperResult]:
        """Perform a single upstream API call."""

    def _handle_http_error(
        self,
        error: HTTPError,
        api_key: str,
        provider_name: str,
    ) -> bool:
        """Handle an HTTPError with API key failover logic.

        Returns ``True`` if the caller should retry with the next key.
        """
        parser = getattr(self, "api_key_parser", None)
        status = error.status_code
        if status in (401, 403):
            if parser is not None:
                parser.mark_key_failed(api_key, f"HTTP {status}", ttl=3600.0)
            logger.warning(
                f"{provider_name} API key auth failed (HTTP {status}), trying next key"
            )
            return True
        if status == 429:
            if parser is not None:
                parser.mark_key_failed(api_key, "rate limited", ttl=300.0)
            logger.warning(f"{provider_name} API rate limit exceeded, trying next key")
            return True
        logger.error(f"{provider_name} API HTTP error {status}: {error.body}")
        return False
