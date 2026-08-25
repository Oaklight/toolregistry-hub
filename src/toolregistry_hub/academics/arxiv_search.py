"""arXiv Search API.

arXiv provides free access to 2.4M+ preprints in physics, mathematics,
computer science, biology, economics, and more.

No API key required. Courtesy rate limit: 1 request per second.

API Documentation: https://info.arxiv.org/help/api/
"""

import re
import threading
import time
import xml.etree.ElementTree as ET
from typing import cast

from .._vendor.httpclient import Client, HTTPError, HttpTimeoutError, Response
from .._vendor.structlog import get_logger
from .base import TIMEOUT_DEFAULT, BaseAcademicSearch
from .paper_result import PaperResult

logger = get_logger()

_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"
_WS_RE = re.compile(r"\s+")


class ArxivSearch(BaseAcademicSearch):
    """arXiv search client with courtesy rate limiting."""

    def __init__(self, rate_limit_delay: float = 1.0):
        self.base_url = "http://export.arxiv.org/api/query"
        self._rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0
        self._lock = threading.Lock()

    def _is_configured(self) -> bool:
        return True

    def _wait_for_rate_limit(self) -> None:
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._rate_limit_delay:
                time.sleep(self._rate_limit_delay - elapsed)
            self._last_request_time = time.time()

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[PaperResult]:
        """Search arXiv for preprints.

        Args:
            query: Search query. Supports arXiv query syntax (e.g.
                ``ti:attention AND au:vaswani``). Plain text queries are
                wrapped with ``all:`` automatically.
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

        search_query = query
        if not any(
            prefix in query for prefix in ("all:", "ti:", "au:", "abs:", "cat:", "co:")
        ):
            search_query = f"all:{query}"

        params = {
            "search_query": search_query,
            "start": "0",
            "max_results": str(max_results),
        }

        self._wait_for_rate_limit()

        try:
            with Client(timeout=timeout) as client:
                response = cast(
                    Response,
                    client.get(self.base_url, params=params),
                )
                response.raise_for_status()
                results = self._parse_results(response.text)
                logger.info(
                    f"arXiv search for '{query}' returned {len(results)} results"
                )
                return results

        except HttpTimeoutError:
            logger.error(f"arXiv API request timed out after {timeout}s")
            return []
        except HTTPError as e:
            logger.error(f"arXiv API HTTP error {e.status_code}: {e.body}")
            return []
        except Exception as e:
            logger.error(f"arXiv API request failed: {e}")
            return []

    def _parse_results(self, raw_results: str) -> list[PaperResult]:
        try:
            root = ET.fromstring(raw_results)
        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv XML: {e}")
            return []

        results = []
        for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
            entry_id = entry.findtext(f"{{{_ATOM_NS}}}id", "")
            if not entry_id or "arxiv.org" not in entry_id:
                continue

            title = _WS_RE.sub(" ", entry.findtext(f"{{{_ATOM_NS}}}title", "")).strip()
            abstract = _WS_RE.sub(
                " ", entry.findtext(f"{{{_ATOM_NS}}}summary", "")
            ).strip()

            authors = [
                name_el.text
                for author in entry.findall(f"{{{_ATOM_NS}}}author")
                if (name_el := author.find(f"{{{_ATOM_NS}}}name")) is not None
                and name_el.text
            ]

            pdf_url = None
            for link in entry.findall(f"{{{_ATOM_NS}}}link"):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break

            published = entry.findtext(f"{{{_ATOM_NS}}}published", "")
            year = int(published[:4]) if len(published) >= 4 else None

            doi = entry.findtext(f"{{{_ARXIV_NS}}}doi")

            category_el = entry.find(f"{{{_ARXIV_NS}}}primary_category")
            venue = category_el.get("term") if category_el is not None else None

            results.append(
                PaperResult(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=entry_id,
                    year=year,
                    venue=venue,
                    doi=doi,
                    pdf_url=pdf_url,
                    source="arxiv",
                )
            )

        return results
