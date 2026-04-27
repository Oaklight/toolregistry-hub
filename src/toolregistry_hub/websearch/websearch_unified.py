"""Unified WebSearch entry point.

Wraps all available search providers behind a single ``search()`` method with an
``engine`` selector. Engines are instantiated lazily and skipped when their API
keys are missing. Supports an ``"auto"`` mode that picks the first configured
engine from a configurable priority list, plus an explicit ``fallback`` flag for
graceful degradation when a chosen engine is unavailable.
"""

from __future__ import annotations

import os
import types
from typing import Literal

from .._vendor.structlog import get_logger
from .base import TIMEOUT_DEFAULT, BaseSearch
from .search_result import SearchResult

logger = get_logger()


# Static type for the ``engine`` parameter. Always exposed in source-level
# tooling and IDE introspection. At instance construction time this may be
# narrowed dynamically to only the actually-configured engines (see
# ``WebSearch.__init__``), so the schema seen by an LLM client reflects the
# real runtime availability.
EngineName = Literal[
    "auto",
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


# Maps engine name → (module path, class name). Lazily imported so unused
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


class WebSearch:
    """Unified web search entry point that dispatches to multiple providers.

    Users can either let the wrapper auto-select the best configured provider
    (``engine="auto"``) or pin a specific engine. Unconfigured engines (missing
    API keys) are skipped automatically. When a specific engine is requested
    but unavailable, the call fails by default — set ``fallback=True`` on a
    per-call basis to fall through to the auto chain instead.

    Example:
        >>> ws = WebSearch()
        >>> ws.search("latest python release", max_results=5)  # auto
        >>> ws.search("latest python release", engine="tavily")  # strict
        >>> ws.search("latest python release", engine="tavily", fallback=True)

    The priority order for ``engine="auto"`` defaults to paid-provider-first
    and can be overridden via the ``WEBSEARCH_PRIORITY`` environment variable
    (comma-separated engine names).
    """

    def __init__(self, priority: str | None = None):
        """Initialize the unified WebSearch wrapper.

        Args:
            priority: Optional comma-separated engine priority. Falls back to
                ``WEBSEARCH_PRIORITY`` env var, then ``_DEFAULT_PRIORITY``.
        """
        self._priority: list[str] = _resolve_priority(priority)
        # Cache instantiated engines (configured ones only)
        self._engine_cache: dict[str, BaseSearch] = {}
        # Narrow the ``engine`` parameter type to only the configured engines
        # so that the JSON schema seen by LLM clients reflects real runtime
        # availability. The class-level full Literal remains intact for IDE /
        # static analysis use.
        self._narrow_engine_annotation()

    def _narrow_engine_annotation(self) -> None:
        """Replace ``self.search`` with a per-instance copy whose ``engine``
        annotation is narrowed to ``Literal["auto", *configured]``.

        Called from ``__init__``. No-op when no engines are configured (the
        unified tool will then be auto-disabled by ``build_registry`` via the
        :class:`Configurable` protocol, so the schema is irrelevant).

        Implementation notes:
            - We construct a fresh ``FunctionType`` from the class method's
              code so that mutating ``__annotations__`` on this copy does not
              affect other instances.
            - The new function is then re-bound to ``self`` as a regular method.
            - ``get_type_hints()`` (used by toolregistry / pydantic for schema
              generation) will see the dynamically-built ``Literal`` instead
              of the deferred string annotation from ``from __future__ import
              annotations``.
        """
        configured = self._configured_engine_names()
        if not configured:
            return  # Nothing to narrow; tool will be auto-disabled anyway

        original = type(self).search
        # Build a fresh function with the same code but isolated annotations.
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
        # Copy then override the engine annotation with the narrowed Literal.
        new_func.__annotations__ = dict(original.__annotations__)
        narrowed_literal = Literal.__getitem__(("auto", *configured))  # type: ignore[arg-type]
        new_func.__annotations__["engine"] = narrowed_literal
        # Bind as method so ``self.search(query, ...)`` works normally.
        self.search = types.MethodType(new_func, self)  # type: ignore[method-assign]

    def _configured_engine_names(self) -> list[str]:
        """Return the priority-ordered list of engine names that are currently configured.

        Returns:
            List of engine names with valid API keys, in priority order.
        """
        return [n for n in self._priority if self._get_engine(n) is not None]

    def _is_configured(self) -> bool:
        """Configured iff at least one underlying engine is configured.

        Used by :func:`build_registry` via the ``Configurable`` protocol to
        auto-disable the unified tool when no providers have keys set.
        """
        return bool(self._configured_engine_names())

    def _get_engine(self, name: str) -> BaseSearch | None:
        """Return a configured engine instance for ``name``, or ``None``.

        Lazily instantiates and caches the engine. Returns ``None`` when the
        engine cannot be constructed or reports itself as unconfigured.

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
        """List all known engines and whether each is currently configured.

        Returns:
            Mapping of engine name → configured status.
        """
        result: dict[str, bool] = {}
        for name in _ENGINE_REGISTRY:
            result[name] = self._get_engine(name) is not None
        return result

    def search(
        self,
        query: str,
        *,
        engine: EngineName = "auto",
        fallback: bool = False,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[SearchResult]:
        """Perform a web search via the selected engine.

        IMPORTANT: For time-sensitive queries (e.g., "recent news", "latest updates",
        "today's events"), you MUST first obtain the current date/time using an
        available time/datetime tool before constructing your search query. As an
        LLM, you have no inherent sense of current time — your training data may
        be outdated. Always verify the current date when temporal context matters.

        Args:
            query: The search query string.
            engine: Provider to use. Either ``"auto"`` (try configured engines
                in priority order) or a specific name from
                ``["brave", "tavily", "searxng", "brightdata", "scrapeless", "serper"]``.
                Note: at runtime this parameter's accepted values are narrowed
                to only the engines whose API keys are configured on this
                instance. Call ``list_engines()`` to inspect availability.
            fallback: When ``engine`` is a specific provider, controls behavior
                if that provider is unavailable or raises. ``False`` (default)
                propagates the error; ``True`` falls back to the auto chain
                excluding the originally-requested engine.
            max_results: Maximum number of results to return (1-20 recommended).
            timeout: Per-request timeout in seconds.
            **kwargs: Provider-specific extra parameters (forwarded as-is).

        Returns:
            List of search results.

        Raises:
            ValueError: If ``engine`` is not a recognized name, or if the query
                is empty.
            RuntimeError: If no engine is available (auto mode), or if the
                requested engine is unavailable and ``fallback=False``.
        """
        if not query or not query.strip():
            return []

        engine = engine.lower().strip()

        if engine == "auto":
            return self._search_auto(
                query,
                exclude=None,
                max_results=max_results,
                timeout=timeout,
                **kwargs,
            )

        if engine not in _ENGINE_REGISTRY:
            raise ValueError(
                f"Unknown websearch engine: {engine!r}. "
                f"Available: {sorted(_ENGINE_REGISTRY)} or 'auto'"
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
                max_results=max_results,
                timeout=timeout,
                **kwargs,
            )

        try:
            return instance.search(
                query, max_results=max_results, timeout=timeout, **kwargs
            )
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
                max_results=max_results,
                timeout=timeout,
                **kwargs,
            )

    def _search_auto(
        self,
        query: str,
        *,
        exclude: set[str] | None = None,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
        **kwargs,
    ) -> list[SearchResult]:
        """Try engines in priority order; return the first successful result.

        Args:
            query: Search query.
            exclude: Engine names to skip.
            max_results: Result cap.
            timeout: Per-request timeout.
            **kwargs: Forwarded to engine.

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
                    query, max_results=max_results, timeout=timeout, **kwargs
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

        # All engines returned empty results
        return []
