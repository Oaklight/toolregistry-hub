"""Unified academic search entry point.

Wraps available academic search providers behind a single ``search()``
method with an ``engine`` selector.

- ``"auto"`` (default) — try engines in priority order, return the first
  successful result.
- ``"<name>"`` — use a specific engine directly.

Engines are instantiated lazily and skipped when their API keys are missing.
"""

from __future__ import annotations

import os
import types
from typing import Literal

from .._vendor.structlog import get_logger
from .base import TIMEOUT_DEFAULT, BaseAcademicSearch
from .paper_result import PaperResult

logger = get_logger()

EngineName = Literal["auto", "openalex", "arxiv"]

_DEFAULT_PRIORITY: tuple[str, ...] = ("openalex", "arxiv")

_ENGINE_REGISTRY: dict[str, tuple[str, str]] = {
    "openalex": ("toolregistry_hub.academics.openalex_search", "OpenAlexSearch"),
    "arxiv": ("toolregistry_hub.academics.arxiv_search", "ArxivSearch"),
}


def _load_engine_class(name: str) -> type[BaseAcademicSearch]:
    if name not in _ENGINE_REGISTRY:
        raise ValueError(
            f"Unknown academic search engine: {name!r}. "
            f"Available: {sorted(_ENGINE_REGISTRY)}"
        )
    module_path, class_name = _ENGINE_REGISTRY[name]
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _resolve_priority(priority: str | None = None) -> list[str]:
    raw = priority or os.getenv("ACADEMIC_SEARCH_PRIORITY")
    if not raw:
        return list(_DEFAULT_PRIORITY)

    names = [p.strip().lower() for p in raw.split(",") if p.strip()]
    valid: list[str] = []
    for n in names:
        if n in _ENGINE_REGISTRY:
            valid.append(n)
        else:
            logger.warning(
                f"Ignoring unknown engine in ACADEMIC_SEARCH_PRIORITY: {n!r}. "
                f"Available: {sorted(_ENGINE_REGISTRY)}"
            )
    return valid or list(_DEFAULT_PRIORITY)


class AcademicSearch:
    """Unified academic search entry point that dispatches to multiple providers.

    Users can let the wrapper auto-select the best configured provider
    (``engine="auto"``), or pin a specific engine (``"openalex"`` or
    ``"arxiv"``). Unconfigured engines (missing API keys) are skipped
    automatically.
    """

    def __init__(self, priority: str | None = None):
        self._priority: list[str] = _resolve_priority(priority)
        self._engine_cache: dict[str, BaseAcademicSearch] = {}
        self._narrow_engine_annotation()

    def _narrow_engine_annotation(self) -> None:
        """Narrow the ``engine`` Literal to only configured providers.

        The toolregistry runtime reads method annotations to generate the
        tool schema exposed to LLM clients. By narrowing the Literal at
        instance construction time, the schema only advertises engines
        that are actually available — preventing the LLM from selecting
        an unconfigured provider.
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
        narrowed_literal = Literal.__getitem__(("auto", *configured))  # type: ignore[arg-type]
        new_func.__annotations__["engine"] = narrowed_literal
        self.search = types.MethodType(new_func, self)  # type: ignore[method-assign]

    def _configured_engine_names(self) -> list[str]:
        return [n for n in self._priority if self._get_engine(n) is not None]

    def _is_configured(self) -> bool:
        return bool(self._configured_engine_names())

    def _get_engine(self, name: str) -> BaseAcademicSearch | None:
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
        """List all known academic search engines and whether each is configured.

        Returns:
            Mapping of engine name to configuration status.
        """
        return {name: self._get_engine(name) is not None for name in _ENGINE_REGISTRY}

    def search(
        self,
        query: str,
        *,
        count: int = 5,
        engine: EngineName = "auto",
        fallback: bool = False,
        timeout: float = TIMEOUT_DEFAULT,
    ) -> list[PaperResult]:
        """Search for academic papers across configured providers.

        Args:
            query: The search query string.
            count: Number of results to return (default 5, max 100).
            engine: Search provider. ``"auto"`` (recommended) tries engines in
                priority order. Set ``"openalex"`` or ``"arxiv"`` to pin a
                specific provider.
            fallback: If True and the chosen engine fails, try the next
                available engine.
            timeout: Request timeout in seconds.

        Returns:
            List of paper results with title, authors, abstract, and metadata.
        """
        if not query or not query.strip():
            return []

        engine = engine.lower().strip()

        if engine == "auto":
            return self._search_auto(query, max_results=count, timeout=timeout)

        if engine not in _ENGINE_REGISTRY:
            raise ValueError(
                f"Unknown academic search engine: {engine!r}. "
                f"Available: {sorted(_ENGINE_REGISTRY)} or 'auto'"
            )

        instance = self._get_engine(engine)
        if instance is None:
            msg = f"Engine {engine!r} is not configured (missing API key)"
            if not fallback:
                raise RuntimeError(msg)
            logger.info(f"{msg}; falling back to auto chain")
            return self._search_auto(
                query, exclude={engine}, max_results=count, timeout=timeout
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
                query, exclude={engine}, max_results=count, timeout=timeout
            )

    def _search_auto(
        self,
        query: str,
        *,
        exclude: set[str] | None = None,
        max_results: int = 5,
        timeout: float = TIMEOUT_DEFAULT,
    ) -> list[PaperResult]:
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
                    query, max_results=max_results, timeout=timeout
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
                "No academic search engines are configured. "
                "arXiv requires no key; for OpenAlex set OPENALEX_API_KEY."
            )

        if last_error is not None:
            raise RuntimeError(
                f"All attempted engines failed ({attempted}). "
                f"Last error: {type(last_error).__name__}: {last_error}"
            ) from last_error

        return []
