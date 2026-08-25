"""OpenAlex Academic Search API.

OpenAlex provides free access to a catalog of 250M+ scholarly works
with metadata including citations, authors, institutions, and open-access links.

Works without any key via the "polite pool" (lower rate limits).
Set OPENALEX_API_KEY for 10x higher daily budget:

    export OPENALEX_API_KEY="your-api-key"

    Free API key available at https://openalex.org/settings/api (instant registration).

Optionally set OPENALEX_MAILTO for polite pool identification:

    export OPENALEX_MAILTO="you@example.com"

API Documentation: https://help.openalex.org/api/
"""

import os
from typing import Any, cast

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError, Response
from .._vendor.structlog import get_logger
from ..utils.api_key_parser import APIKeyParser
from .base import TIMEOUT_DEFAULT, BaseAcademicSearch
from .paper_result import PaperResult

logger = get_logger()

_SELECT_FIELDS = ",".join(
    [
        "id",
        "doi",
        "display_name",
        "publication_year",
        "authorships",
        "cited_by_count",
        "primary_location",
        "open_access",
        "abstract_inverted_index",
    ]
)


class OpenAlexSearch(BaseAcademicSearch):
    """OpenAlex academic search client.

    Works without a key via the polite pool. Set ``OPENALEX_API_KEY`` for
    10x higher daily budget. Set ``OPENALEX_MAILTO`` for polite pool
    identification when no key is configured.
    """

    def __init__(
        self,
        api_keys: str | None = None,
        rate_limit_delay: float = 0.1,
        mailto: str | None = None,
    ):
        self.api_key_parser = APIKeyParser(
            api_keys=api_keys,
            env_var_name="OPENALEX_API_KEY",
            rate_limit_delay=rate_limit_delay,
        )
        self.base_url = "https://api.openalex.org"
        self._mailto = mailto or os.getenv("OPENALEX_MAILTO", "")

    def _is_configured(self) -> bool:
        """Always configured — polite pool works without a key."""
        return True

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[PaperResult]:
        """Search OpenAlex for academic papers.

        Args:
            query: Search query string.
            max_results: Maximum number of results (1-100).
            timeout: Request timeout in seconds.

        Returns:
            List of paper results.
        """
        if not query.strip():
            return []
        max_results = min(max_results, 100)
        results = self._search_impl(
            query, max_results=max_results, timeout=timeout, **kwargs
        )
        return results[:max_results]

    def _search_impl(self, query: str, **kwargs) -> list[PaperResult]:
        max_results = kwargs.get("max_results", 5)
        timeout = kwargs.get("timeout", TIMEOUT_DEFAULT)

        has_keys = bool(self.api_key_parser.api_keys)
        if has_keys:
            return self._search_with_keys(query, max_results, timeout)
        return self._search_polite(query, max_results, timeout)

    def _search_with_keys(
        self, query: str, max_results: int, timeout: float
    ) -> list[PaperResult]:
        max_attempts = self.api_key_parser.key_count

        for _attempt in range(max_attempts):
            try:
                api_key = self.api_key_parser.get_next_valid_key()
            except ValueError:
                logger.error("All OpenAlex API keys are currently unavailable")
                break

            self.api_key_parser.wait_for_rate_limit(api_key=api_key)

            params: dict[str, Any] = {
                "search": query,
                "per_page": max_results,
                "api_key": api_key,
                "select": _SELECT_FIELDS,
            }

            try:
                return self._do_request(query, params, timeout)
            except HttpTimeoutError:
                raise
            except HTTPError as e:
                if self._handle_http_error(e, api_key, "OpenAlex"):
                    continue
                raise

        return []

    def _search_polite(
        self, query: str, max_results: int, timeout: float
    ) -> list[PaperResult]:
        params: dict[str, Any] = {
            "search": query,
            "per_page": max_results,
            "select": _SELECT_FIELDS,
        }
        if self._mailto:
            params["mailto"] = self._mailto
        return self._do_request(query, params, timeout)

    def _do_request(
        self, query: str, params: dict[str, Any], timeout: float
    ) -> list[PaperResult]:
        with Client(timeout=timeout) as client:
            response = cast(
                Response,
                client.get(f"{self.base_url}/works", params=params),
            )
            response.raise_for_status()
            data = response.json()
            results = self._parse_results(data)
            logger.info(
                f"OpenAlex search for '{query}' returned {len(results)} results"
            )
            return results

    def _parse_results(self, raw_results: dict) -> list[PaperResult]:
        results = []
        for work in raw_results.get("results", []):
            authors = [
                a.get("author", {}).get("display_name", "")
                for a in work.get("authorships", [])
                if a.get("author", {}).get("display_name")
            ]

            location = work.get("primary_location") or {}
            source = location.get("source") or {}
            venue = source.get("display_name")

            oa = work.get("open_access") or {}
            pdf_url = oa.get("oa_url")

            doi = work.get("doi")

            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

            results.append(
                PaperResult(
                    title=work.get("display_name", ""),
                    authors=authors,
                    abstract=abstract,
                    url=work.get("id", ""),
                    year=work.get("publication_year"),
                    venue=venue,
                    doi=doi,
                    pdf_url=pdf_url,
                    cited_by_count=work.get("cited_by_count"),
                    source="openalex",
                )
            )
        return results

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
        """Reconstruct readable abstract from OpenAlex inverted index format.

        OpenAlex stores abstracts as ``{"word": [pos1, pos2, ...], ...}``.
        This inverts the mapping and joins words by position.
        """
        if not inverted_index:
            return ""
        word_positions: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        return " ".join(word for _, word in word_positions)
