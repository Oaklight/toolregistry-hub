"""Tests for the unified WebSearch entry point.

Covers engine="auto" (priority chain), engine="<specific>" (strict and
fallback modes), priority configuration via env var, and the
``_is_configured`` protocol used by ``build_registry``.
"""

from __future__ import annotations

from typing import get_args, get_type_hints
from unittest.mock import MagicMock, patch

import pytest

from toolregistry_hub.websearch.search_result import SearchResult
from toolregistry_hub.websearch.websearch_unified import (
    _DEFAULT_PRIORITY,
    _ENGINE_REGISTRY,
    EngineName,
    WebSearch,
    _resolve_priority,
)


def _make_result(title: str = "t", url: str = "u", content: str = "c") -> SearchResult:
    return SearchResult(title=title, url=url, content=content, score=1.0)


@pytest.fixture
def mock_engines(monkeypatch):
    """Replace ``_get_engine`` with a controllable mock map.

    Returns a ``dict`` that the test can mutate; setting a value to ``None``
    simulates an unconfigured engine, while a ``MagicMock`` simulates a working
    one. Default: all engines unconfigured.
    """
    state: dict[str, MagicMock | None] = dict.fromkeys(_ENGINE_REGISTRY)

    def fake_get_engine(self, name: str):
        return state.get(name)

    monkeypatch.setattr(WebSearch, "_get_engine", fake_get_engine)
    return state


# ---------------------------------------------------------------------------
# Priority resolution
# ---------------------------------------------------------------------------


class TestResolvePriority:
    def test_default_when_nothing_set(self, monkeypatch):
        monkeypatch.delenv("WEBSEARCH_PRIORITY", raising=False)
        assert _resolve_priority() == list(_DEFAULT_PRIORITY)

    def test_env_var_overrides_default(self, monkeypatch):
        monkeypatch.setenv("WEBSEARCH_PRIORITY", "searxng,brave")
        assert _resolve_priority() == ["searxng", "brave"]

    def test_explicit_arg_overrides_env(self, monkeypatch):
        monkeypatch.setenv("WEBSEARCH_PRIORITY", "tavily")
        assert _resolve_priority("brave,searxng") == ["brave", "searxng"]

    def test_unknown_engines_dropped(self, monkeypatch):
        monkeypatch.delenv("WEBSEARCH_PRIORITY", raising=False)
        assert _resolve_priority("brave,unknown_xyz,searxng") == ["brave", "searxng"]

    def test_all_unknown_falls_back_to_default(self, monkeypatch):
        monkeypatch.delenv("WEBSEARCH_PRIORITY", raising=False)
        assert _resolve_priority("nope,nada") == list(_DEFAULT_PRIORITY)

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.delenv("WEBSEARCH_PRIORITY", raising=False)
        assert _resolve_priority("BRAVE,Tavily") == ["brave", "tavily"]


# ---------------------------------------------------------------------------
# is_configured / list_engines
# ---------------------------------------------------------------------------


class TestIsConfigured:
    def test_no_engines_configured(self, mock_engines):
        ws = WebSearch()
        assert ws._is_configured() is False

    def test_at_least_one_configured(self, mock_engines):
        mock_engines["brave"] = MagicMock()
        ws = WebSearch()
        assert ws._is_configured() is True

    def test_list_engines_reports_status(self, mock_engines):
        mock_engines["brave"] = MagicMock()
        mock_engines["searxng"] = MagicMock()
        ws = WebSearch()
        status = ws.list_engines()
        assert status["brave"] is True
        assert status["searxng"] is True
        assert status["tavily"] is False


# ---------------------------------------------------------------------------
# search() — auto mode
# ---------------------------------------------------------------------------


class TestSearchAuto:
    def test_empty_query_returns_empty(self, mock_engines):
        ws = WebSearch()
        assert ws.search("") == []
        assert ws.search("   ") == []

    def test_no_engines_raises(self, mock_engines):
        ws = WebSearch()
        with pytest.raises(RuntimeError, match="No websearch engines"):
            ws.search("python")

    def test_auto_uses_first_configured_in_priority(self, mock_engines):
        # tavily is first in default priority
        tavily = MagicMock()
        tavily.search.return_value = [_make_result("tavily-result")]
        mock_engines["tavily"] = tavily
        # brave also configured but lower priority
        brave = MagicMock()
        mock_engines["brave"] = brave

        ws = WebSearch()
        results = ws.search("python")
        assert results[0].title == "tavily-result"
        tavily.search.assert_called_once()
        brave.search.assert_not_called()

    def test_auto_skips_unconfigured(self, mock_engines):
        # Only searxng configured (last in priority)
        searxng = MagicMock()
        searxng.search.return_value = [_make_result("searxng-result")]
        mock_engines["searxng"] = searxng

        ws = WebSearch()
        results = ws.search("python")
        assert results[0].title == "searxng-result"

    def test_auto_falls_through_on_empty_results(self, mock_engines):
        tavily = MagicMock()
        tavily.search.return_value = []
        mock_engines["tavily"] = tavily

        brave = MagicMock()
        brave.search.return_value = [_make_result("brave-result")]
        mock_engines["brave"] = brave

        ws = WebSearch()
        results = ws.search("python")
        assert results[0].title == "brave-result"

    def test_auto_falls_through_on_exception(self, mock_engines):
        tavily = MagicMock()
        tavily.search.side_effect = RuntimeError("rate limit")
        mock_engines["tavily"] = tavily

        brave = MagicMock()
        brave.search.return_value = [_make_result("brave-result")]
        mock_engines["brave"] = brave

        ws = WebSearch()
        results = ws.search("python")
        assert results[0].title == "brave-result"

    def test_auto_all_fail_raises_with_last_error(self, mock_engines):
        tavily = MagicMock()
        tavily.search.side_effect = RuntimeError("first error")
        brave = MagicMock()
        brave.search.side_effect = RuntimeError("last error")
        mock_engines["tavily"] = tavily
        mock_engines["brave"] = brave

        ws = WebSearch()
        with pytest.raises(RuntimeError, match="last error"):
            ws.search("python")

    def test_auto_all_empty_returns_empty(self, mock_engines):
        for name in ("tavily", "brave"):
            m = MagicMock()
            m.search.return_value = []
            mock_engines[name] = m

        ws = WebSearch()
        assert ws.search("python") == []


# ---------------------------------------------------------------------------
# search() — specific engine
# ---------------------------------------------------------------------------


class TestSearchSpecificEngine:
    def test_unknown_engine_raises(self, mock_engines):
        ws = WebSearch()
        with pytest.raises(ValueError, match="Unknown websearch engine"):
            ws.search("python", engine="bing")

    def test_specific_engine_runs_only_that_engine(self, mock_engines):
        brave = MagicMock()
        brave.search.return_value = [_make_result("brave-result")]
        mock_engines["brave"] = brave
        # Tavily configured too — must not be called when engine="brave"
        mock_engines["tavily"] = MagicMock()

        ws = WebSearch()
        results = ws.search("python", engine="brave")
        assert results[0].title == "brave-result"
        brave.search.assert_called_once()
        mock_engines["tavily"].search.assert_not_called()

    def test_unconfigured_engine_strict_raises(self, mock_engines):
        ws = WebSearch()
        with pytest.raises(RuntimeError, match="not configured"):
            ws.search("python", engine="brave")

    def test_unconfigured_engine_with_fallback_uses_auto(self, mock_engines):
        # brave NOT configured, fallback should land on searxng
        searxng = MagicMock()
        searxng.search.return_value = [_make_result("searxng-result")]
        mock_engines["searxng"] = searxng

        ws = WebSearch()
        results = ws.search("python", engine="brave", fallback=True)
        assert results[0].title == "searxng-result"

    def test_engine_failure_strict_propagates(self, mock_engines):
        brave = MagicMock()
        brave.search.side_effect = RuntimeError("brave api down")
        mock_engines["brave"] = brave

        ws = WebSearch()
        with pytest.raises(RuntimeError, match="brave api down"):
            ws.search("python", engine="brave")

    def test_engine_failure_with_fallback_excludes_failed(self, mock_engines):
        brave = MagicMock()
        brave.search.side_effect = RuntimeError("brave api down")
        mock_engines["brave"] = brave

        # Fallback chain — tavily configured and works
        tavily = MagicMock()
        tavily.search.return_value = [_make_result("tavily-result")]
        mock_engines["tavily"] = tavily

        ws = WebSearch()
        results = ws.search("python", engine="brave", fallback=True)
        assert results[0].title == "tavily-result"
        # brave was tried once originally and excluded from fallback chain
        brave.search.assert_called_once()
        tavily.search.assert_called_once()

    def test_engine_name_case_insensitive(self, mock_engines):
        brave = MagicMock()
        brave.search.return_value = [_make_result("brave-result")]
        mock_engines["brave"] = brave

        ws = WebSearch()
        results = ws.search("python", engine="BRAVE")
        assert results[0].title == "brave-result"

    def test_kwargs_forwarded(self, mock_engines):
        brave = MagicMock()
        brave.search.return_value = []
        mock_engines["brave"] = brave

        ws = WebSearch()
        ws.search(
            "python",
            engine="brave",
            max_results=10,
            timeout=30.0,
            country="US",
        )
        brave.search.assert_called_once_with(
            "python", max_results=10, timeout=30.0, country="US"
        )


# ---------------------------------------------------------------------------
# Engine loading (real import paths)
# ---------------------------------------------------------------------------


class TestEngineLoading:
    """These tests stub ``_load_engine_class`` BEFORE constructing ``WebSearch``
    so that ``__init__`` (which warms the engine cache via the annotation
    narrowing pass) sees the stub rather than any real provider classes that
    may pick up live API keys from the test environment.
    """

    def test_get_engine_caches(self):
        """Once instantiated, ``_get_engine`` should return the cached instance."""
        instance = MagicMock()
        instance._is_configured.return_value = True
        fake_cls = MagicMock(return_value=instance)

        with patch(
            "toolregistry_hub.websearch.websearch_unified._load_engine_class",
            return_value=fake_cls,
        ):
            ws = WebSearch()
            first = ws._get_engine("brave")
            second = ws._get_engine("brave")

        assert first is second
        # __init__ warms the cache for every engine in the priority list (one
        # construction call per priority entry); after that, repeat lookups
        # for "brave" must hit the cache rather than re-instantiate.
        assert fake_cls.call_count == len(ws._priority)

    def test_get_engine_returns_none_when_unconfigured(self):
        instance = MagicMock()
        instance._is_configured.return_value = False
        fake_cls = MagicMock(return_value=instance)

        with patch(
            "toolregistry_hub.websearch.websearch_unified._load_engine_class",
            return_value=fake_cls,
        ):
            ws = WebSearch()
            assert ws._get_engine("brave") is None

    def test_get_engine_returns_none_on_construction_failure(self):
        fake_cls = MagicMock(side_effect=ValueError("missing keys"))

        with patch(
            "toolregistry_hub.websearch.websearch_unified._load_engine_class",
            return_value=fake_cls,
        ):
            ws = WebSearch()
            assert ws._get_engine("brave") is None


# ---------------------------------------------------------------------------
# Dynamic engine annotation narrowing (B+C scheme)
# ---------------------------------------------------------------------------


class TestEngineAnnotationNarrowing:
    """Verify the per-instance ``engine`` annotation is narrowed to only the
    configured engines. This is what allows LLM clients to see a JSON schema
    enum that reflects real runtime availability rather than the full menu.
    """

    def test_static_class_literal_is_full(self):
        """Class-level ``EngineName`` keeps the full set for IDE / type checkers."""
        full = set(get_args(EngineName))
        assert full == {"auto", *_ENGINE_REGISTRY}

    def test_no_narrowing_when_no_engines_configured(self, mock_engines):
        """No engines configured → no override; class-level annotation remains."""
        ws = WebSearch()
        # search is still the class method (no per-instance copy)
        assert ws.search.__func__ is WebSearch.search

    def test_narrowing_happens_when_one_engine_configured(self, mock_engines):
        mock_engines["brave"] = MagicMock()
        ws = WebSearch()
        # Per-instance copy was bound
        assert ws.search.__func__ is not WebSearch.search
        engine_anno = ws.search.__func__.__annotations__["engine"]
        assert set(get_args(engine_anno)) == {"auto", "brave"}

    def test_narrowing_includes_only_configured_in_priority_order(self, mock_engines):
        # Configure brave, tavily, searxng
        for name in ("brave", "tavily", "searxng"):
            mock_engines[name] = MagicMock()
        ws = WebSearch()
        engine_anno = ws.search.__func__.__annotations__["engine"]
        narrowed = get_args(engine_anno)
        # "auto" first, then engines in default priority order
        assert narrowed[0] == "auto"
        assert set(narrowed) == {"auto", "brave", "tavily", "searxng"}

    def test_narrowing_is_per_instance(self, mock_engines):
        """Mutating one instance's engines should not affect another."""
        mock_engines["brave"] = MagicMock()
        ws1 = WebSearch()
        anno1 = ws1.search.__func__.__annotations__["engine"]

        # Add a second engine; new instance picks it up but ws1 stays narrowed
        mock_engines["tavily"] = MagicMock()
        ws2 = WebSearch()
        anno2 = ws2.search.__func__.__annotations__["engine"]

        assert set(get_args(anno1)) == {"auto", "brave"}
        assert set(get_args(anno2)) == {"auto", "brave", "tavily"}

    def test_get_type_hints_returns_narrowed_literal(self, mock_engines):
        """Confirms toolregistry/pydantic schema generators see the narrowed type."""
        mock_engines["brave"] = MagicMock()
        ws = WebSearch()
        hints = get_type_hints(ws.search.__func__)
        engine_hint = hints["engine"]
        assert set(get_args(engine_hint)) == {"auto", "brave"}

    def test_narrowed_search_still_callable(self, mock_engines):
        """The replacement function must work as a normal bound method."""
        brave = MagicMock()
        brave.search.return_value = [_make_result("ok")]
        mock_engines["brave"] = brave

        ws = WebSearch()
        results = ws.search("python", engine="brave")
        assert results[0].title == "ok"

    def test_narrowing_respects_custom_priority(self, mock_engines, monkeypatch):
        """Narrowed list should include only configured engines from the priority."""
        monkeypatch.setenv("WEBSEARCH_PRIORITY", "searxng,brave")
        mock_engines["brave"] = MagicMock()
        # tavily is configured but NOT in the priority list — must be excluded
        mock_engines["tavily"] = MagicMock()

        ws = WebSearch()
        engine_anno = ws.search.__func__.__annotations__["engine"]
        narrowed = set(get_args(engine_anno))
        assert narrowed == {"auto", "brave"}
        assert "tavily" not in narrowed
