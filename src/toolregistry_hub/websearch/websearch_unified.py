"""Unified WebSearch entry point.

Wraps all available search providers behind a single ``search()`` method with an
``engine`` selector.  Three modes:

- ``"auto"`` (default) — try engines sequentially in priority order, return
  the first successful result.
- ``"parallel"`` — query multiple engines concurrently, deduplicate and
  re-rank results with BM25 scoring.
- ``"<name>"`` — use a specific engine directly.

Engines are instantiated lazily and skipped when their API keys are missing.
"""

from __future__ import annotations

import os
import types
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

from .._vendor.structlog import get_logger
from .base import TIMEOUT_DEFAULT, BaseSearch
from .dedup import deduplicate_results
from .search_result import SearchResult

logger = get_logger()


# Static type for the ``engine`` parameter. Always exposed in source-level
# tooling and IDE introspection. At instance construction time this may be
# narrowed dynamically to only the actually-configured engines (see
# ``WebSearch.__init__``), so the schema seen by an LLM client reflects the
# real runtime availability.
EngineName = Literal[
    "auto",
    "parallel",
    "brave",
    "tavily",
    "searxng",
    "brightdata",
    "scrapeless",
    "serper",
]


# Default engine priority for the "auto" mode. Paid / higher-quality providers
# come first so that "auto" yields the best results when keys are available.
# Override at runtime via the ``WEBSEARCH_PRIORITY`` environment variable
# (comma-separated names, e.g. ``"searxng,brave,tavily"``).
_DEFAULT_PRIORITY: tuple[str, ...] = (
    "tavily",
    "brave",
    "serper",
    "brightdata",
    "scrapeless",
    "searxng",
)

# Default engines to query in parallel mode.
# Override via ``WEBSEARCH_PARALLEL_ENGINES`` env var (comma-separated).
_DEFAULT_PARALLEL_ENGINES: tuple[str, ...] = ("brightdata", "brave")


# Maps engine name -> (module path, class name). Lazily imported so unused
# providers don't pay the import cost.
_ENGINE_REGISTRY: dict[str, tuple[str, str]] = {
    "brave": ("toolregistry_hub.websearch.websearch_brave", "BraveSearch"),
    "tavily": ("toolregistry_hub.websearch.websearch_tavily", "TavilySearch"),
    "searxng": ("toolregistry_hub.websearch.websearch_searxng", "SearXNGSearch"),
    "brightdata": (
        "toolregistry_hub.websearch.websearch_brightdata",
        "BrightDataSearch",
    ),
    "scrapeless": (
        "toolregistry_hub.websearch.websearch_scrapeless",
        "ScrapelessSearch",
    ),
    "serper": ("toolregistry_hub.websearch.websearch_serper", "SerperSearch"),
}


def _load_engine_class(name: str) -> type[BaseSearch]:
    """Import and return the engine class for ``name``.

    Args:
        name: Engine identifier (e.g. ``"brave"``).

    Returns:
        The provider class.

    Raises:
        ValueError: If ``name`` is not a known engine.
        ImportError: If the engine module cannot be imported.
    """
    if name not in _ENGINE_REGISTRY:
        raise ValueError(
            f"Unknown websearch engine: {name!r}. Available: {sorted(_ENGINE_REGISTRY)}"
        )
    module_path, class_name = _ENGINE_REGISTRY[name]
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _resolve_priority(priority: str | None = None) -> list[str]:
    """Resolve the engine priority order.

    Lookup order:
        1. Explicit ``priority`` argument (comma-separated string)
        2. ``WEBSEARCH_PRIORITY`` environment variable
        3. ``_DEFAULT_PRIORITY``

    Unknown engine names are silently dropped with a warning.

    Args:
        priority: Optional comma-separated engine names.

    Returns:
        Ordered list of valid engine names.
    """
    raw = priority or os.getenv("WEBSEARCH_PRIORITY")
    if not raw:
        return list(_DEFAULT_PRIORITY)

    names = [p.strip().lower() for p in raw.split(",") if p.strip()]
    valid: list[str] = []
    for n in names:
        if n in _ENGINE_REGISTRY:
            valid.append(n)
        else:
            logger.warning(
                f"Ignoring unknown engine in WEBSEARCH_PRIORITY: {n!r}. "
                f"Available: {sorted(_ENGINE_REGISTRY)}"
            )
    return valid or list(_DEFAULT_PRIORITY)


def _resolve_parallel_engines() -> list[str]:
    """Resolve which engines to use in parallel mode.

    Reads from ``WEBSEARCH_PARALLEL_ENGINES`` env var (comma-separated),
    falling back to ``_DEFAULT_PARALLEL_ENGINES``.

    Returns:
        List of valid engine names for parallel queries.
    """
    raw = os.getenv("WEBSEARCH_PARALLEL_ENGINES")
    if not raw:
        return list(_DEFAULT_PARALLEL_ENGINES)

    names = [p.strip().lower() for p in raw.split(",") if p.strip()]
    valid = [n for n in names if n in _ENGINE_REGISTRY]
    if not valid:
        logger.warning(
            "WEBSEARCH_PARALLEL_ENGINES contained no valid engines; using defaults"
        )
        return list(_DEFAULT_PARALLEL_ENGINES)
    return valid


class WebSearch:
    """Unified web search entry point that dispatches to multiple providers.

    Users can either let the wrapper auto-select the best configured provider
    (``engine="auto"``), query multiple engines in parallel for higher quality
    results (``engine="parallel"``), or pin a specific engine.  Unconfigured
    engines (missing API keys) are skipped automatically.
    """

    def __init__(self, priority: str | None = None):
        """Initialize the unified WebSearch wrapper.

        Args:
            priority: Optional comma-separated engine priority. Falls back to
                ``WEBSEARCH_PRIORITY`` env var, then ``_DEFAULT_PRIORITY``.
        """
        self._priority: list[str] = _resolve_priority(priority)
        self._parallel_engines: list[str] = _resolve_parallel_engines()
        # Cache instantiated engines (configured ones only)
        self._engine_cache: dict[str, BaseSearch] = {}
        # Narrow the ``engine`` parameter type to only the configured engines
        self._narrow_engine_annotation()

    def _narrow_engine_annotation(self) -> None:
        """Replace ``self.search`` with a per-instance copy whose ``engine``
        annotation is narrowed to ``Literal["auto", "parallel", *configured]``.

        Called from ``__init__``. No-op when no engines are configured.
        """
        configured = self._configured_engine_names()
        if not configured:
            return

        original = type(self).search
        new_func = types.FunctionType(
            original.__code__,
            original.__globals__,
            name=original.__name__,
            argdefs=original.__defaults__,
            closure=original.__closure__,
        )
        new_func.__doc__ = original.__doc__
        new_func.__qualname__ = original.__qualname__
        new_func.__kwdefaults__ = original.__kwdefaults__
        new_func.__annotations__ = dict(original.__annotations__)
        narrowed_literal = Literal.__getitem__(("auto", "parallel", *configured))  # type: ignore[arg-type]
        new_func.__annotations__["engine"] = narrowed_literal
        self.search = types.MethodType(new_func, self)  # type: ignore[method-assign]

    def _configured_engine_names(self) -> list[str]:
        """Return the priority-ordered list of engine names that are configured.

        Returns:
            List of engine names with valid API keys, in priority order.
        """
        return [n for n in self._priority if self._get_engine(n) is not None]

    def _is_configured(self) -> bool:
        """Configured iff at least one underlying engine is configured."""
        return bool(self._configured_engine_names())

    def _get_engine(self, name: str) -> BaseSearch | None:
        """Return a configured engine instance for ``name``, or ``None``.

        Lazily instantiates and caches the engine.

        Args:
            name: Engine identifier.

        Returns:
            Configured ``BaseSearch`` instance, or ``None``.
        """
        if name in self._engine_cache:
            return self._engine_cache[name]

        try:
            cls = _load_engine_class(name)
            instance = cls()
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Failed to construct engine {name!r}: {e}")
            return None

        if not instance._is_configured():
            logger.debug(f"Engine {name!r} is not configured (missing API key)")
            return None

        self._engine_cache[name] = instance
        return instance

    def list_engines(self) -> dict[str, bool]:
        """List all known search engines and whether each is currently configured.

        Returns:
            Mapping of engine name -> True if the engine has valid API keys
            and is ready to use, False otherwise.
        """
        result: dict[str, bool] = {}
        for name in _ENGINE_REGISTRY:
            result[name] = self._get_engine(name) is not None
        return result

    def search(
        self,
        query: str,
        *,
        count: int = 5,
        engine: EngineName = "auto",
        fallback: bool = False,
        timeout: float = TIMEOUT_DEFAULT,
    ) -> list[SearchResult]:
        """Perform a web search via the selected engine.

        This is the primary tool for web search. Just pass a query — the
        engine is selected automatically from configured providers (Brave,
        Tavily, SearXNG, etc.) with built-in fallback. You do NOT need to
        pick a specific engine unless you have a reason to.

        Use ``engine="parallel"`` to query multiple engines simultaneously
        and get deduplicated, BM25-ranked results for higher quality.

        IMPORTANT: For time-sensitive queries (e.g., "recent news", "latest
        updates", "today's events"), first obtain the current date/time using
        the datetime tool. You have no inherent sense of current time.

        Args:
            query: The search query string.
            count: Number of results to return (default 5, max 20).
            engine: Search provider. Leave as ``"auto"`` (recommended) to let
                the server pick the best available engine. Use ``"parallel"``
                to query multiple engines and merge results. Only set a
                specific engine name if you need a particular provider.
            fallback: If True and the chosen engine fails, automatically try
                the next available engine instead of raising an error.
                Ignored when ``engine="parallel"`` (parallel mode has
                built-in per-engine error handling).
            timeout: Request timeout in seconds.

        Returns:
            List of search results, each with title, url, content, and score.
        """
        if not query or not query.strip():
            return []

        engine = engine.lower().strip()

        if engine == "auto":
            return self._search_auto(
                query,
                exclude=None,
                max_results=count,
                timeout=timeout,
            )

        if engine == "parallel":
            return self._search_parallel(
                query,
                max_results=count,
                timeout=timeout,
            )

        if engine not in _ENGINE_REGISTRY:
            raise ValueError(
                f"Unknown websearch engine: {engine!r}. "
                f"Available: {sorted(_ENGINE_REGISTRY)} or 'auto' or 'parallel'"
            )

        instance = self._get_engine(engine)
        if instance is None:
            msg = f"Engine {engine!r} is not configured (missing API key)"
            if not fallback:
                raise RuntimeError(msg)
            logger.info(f"{msg}; falling back to auto chain")
            return self._search_auto(
                query,
                exclude={engine},
                max_results=count,
                timeout=timeout,
            )

        try:
            return instance.search(query, max_results=count, timeout=timeout)
        except Exception as e:  # noqa: BLE001
            if not fallback:
                raise
            logger.warning(
                f"Engine {engine!r} raised {type(e).__name__}: {e}; "
                f"falling back to auto chain"
            )
            return self._search_auto(
                query,
                exclude={engine},
                max_results=count,
                timeout=timeout,
            )

    # ── Internal strategies ──────────────────────────────────────────────

    def _search_auto(
        self,
        query: str,
        *,
        exclude: set[str] | None = None,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
    ) -> list[SearchResult]:
        """Try engines in priority order; return the first successful result.

        Automatically skips unconfigured and failing engines.

        Args:
            query: Search query.
            exclude: Engine names to skip.
            max_results: Result cap.
            timeout: Per-request timeout.

        Returns:
            Search results from the first successful engine.

        Raises:
            RuntimeError: If no configured engine succeeds.
        """
        skip = exclude or set()
        last_error: Exception | None = None
        attempted: list[str] = []

        for name in self._priority:
            if name in skip:
                continue
            instance = self._get_engine(name)
            if instance is None:
                continue
            attempted.append(name)
            try:
                logger.debug(f"Trying engine {name!r} for query {query!r}")
                results = instance.search(
                    query,
                    max_results=max_results,
                    timeout=timeout,
                )
                if results:
                    return results
                logger.debug(f"Engine {name!r} returned no results; trying next")
            except Exception as e:  # noqa: BLE001
                last_error = e
                logger.debug(
                    f"Engine {name!r} raised {type(e).__name__}: {e}; trying next"
                )

        if not attempted:
            raise RuntimeError(
                "No websearch engines are configured. Set at least one of: "
                f"{sorted(f'{n.upper()}_API_KEY' for n in _ENGINE_REGISTRY)}"
            )

        if last_error is not None:
            raise RuntimeError(
                f"All attempted engines failed ({attempted}). "
                f"Last error: {type(last_error).__name__}: {last_error}"
            ) from last_error

        return []

    def _search_parallel(
        self,
        query: str,
        *,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
    ) -> list[SearchResult]:
        """Query multiple engines concurrently, deduplicate, and re-rank.

        Engines are read from ``WEBSEARCH_PARALLEL_ENGINES`` (default:
        ``brightdata,brave``).  Unconfigured engines are skipped.  Individual
        engine failures are logged but do not abort the search — results from
        successful engines are still returned.

        Args:
            query: Search query.
            max_results: Maximum number of results after deduplication.
            timeout: Per-engine timeout.

        Returns:
            Deduplicated, BM25-ranked results from all successful engines.

        Raises:
            RuntimeError: If no parallel engines are configured.
        """
        # Resolve which engines to use, skipping unconfigured ones.
        engines: list[tuple[str, BaseSearch]] = []
        for name in self._parallel_engines:
            instance = self._get_engine(name)
            if instance is not None:
                engines.append((name, instance))

        if not engines:
            logger.info("No parallel engines configured; falling back to auto")
            return self._search_auto(
                query,
                max_results=max_results,
                timeout=timeout,
            )

        # Query all engines concurrently.
        all_results: list[SearchResult] = []
        engine_names = [name for name, _ in engines]
        logger.debug(f"Parallel search with engines: {engine_names}")

        with ThreadPoolExecutor(max_workers=len(engines)) as pool:
            futures = {
                pool.submit(
                    inst.search,
                    query,
                    max_results=max_results,
                    timeout=timeout,
                ): name
                for name, inst in engines
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                        logger.debug(f"Engine {name!r} returned {len(results)} results")
                    else:
                        logger.debug(f"Engine {name!r} returned no results")
                except Exception as e:  # noqa: BLE001
                    logger.warning(
                        f"Parallel engine {name!r} failed: {type(e).__name__}: {e}"
                    )

        if not all_results:
            logger.info("All parallel engines returned empty; falling back to auto")
            return self._search_auto(
                query,
                max_results=max_results,
                timeout=timeout,
            )

        # Deduplicate and re-rank with BM25.
        deduped = deduplicate_results(all_results, query)
        return deduped[:max_results]
