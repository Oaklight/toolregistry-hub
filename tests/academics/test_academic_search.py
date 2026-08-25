"""Unit tests for AcademicSearch unified dispatcher."""

from unittest.mock import MagicMock, patch

import pytest

from toolregistry_hub.academics.academic_search import (
    _DEFAULT_PRIORITY,
    _ENGINE_REGISTRY,
    AcademicSearch,
    _resolve_priority,
)
from toolregistry_hub.academics.paper_result import PaperResult


def _make_paper(title="Test Paper", source="openalex"):
    return PaperResult(
        title=title,
        authors=["Author"],
        abstract="Abstract",
        url="https://example.com",
        source=source,
    )


class TestResolvePriority:
    def test_default(self):
        assert _resolve_priority() == list(_DEFAULT_PRIORITY)

    @patch.dict("os.environ", {"ACADEMIC_SEARCH_PRIORITY": "arxiv,openalex"})
    def test_from_env(self):
        assert _resolve_priority() == ["arxiv", "openalex"]

    def test_explicit_arg(self):
        assert _resolve_priority("arxiv") == ["arxiv"]

    def test_unknown_engines_dropped(self):
        result = _resolve_priority("arxiv,unknown,openalex")
        assert result == ["arxiv", "openalex"]

    def test_all_unknown_falls_back_to_default(self):
        result = _resolve_priority("unknown1,unknown2")
        assert result == list(_DEFAULT_PRIORITY)


class TestAcademicSearchInit:
    def test_engine_registry_keys(self):
        assert "openalex" in _ENGINE_REGISTRY
        assert "arxiv" in _ENGINE_REGISTRY

    def test_is_configured_with_arxiv(self):
        search = AcademicSearch()
        assert search._is_configured() is True

    def test_list_engines(self):
        search = AcademicSearch()
        engines = search.list_engines()
        assert "arxiv" in engines
        assert engines["arxiv"] is True


class TestSearchAuto:
    def test_empty_query(self):
        search = AcademicSearch()
        assert search.search("") == []

    def test_auto_returns_first_configured(self):
        search = AcademicSearch()
        mock_engine = MagicMock()
        mock_engine._is_configured.return_value = True
        mock_engine.search.return_value = [_make_paper()]
        search._engine_cache["openalex"] = mock_engine

        results = search.search("test", engine="auto")
        assert len(results) == 1
        mock_engine.search.assert_called_once()

    def test_auto_skips_empty_results(self):
        search = AcademicSearch()
        mock_empty = MagicMock()
        mock_empty._is_configured.return_value = True
        mock_empty.search.return_value = []

        mock_arxiv = MagicMock()
        mock_arxiv._is_configured.return_value = True
        mock_arxiv.search.return_value = [_make_paper(source="arxiv")]

        search._engine_cache["openalex"] = mock_empty
        search._engine_cache["arxiv"] = mock_arxiv

        results = search.search("test", engine="auto")
        assert len(results) == 1
        assert results[0].source == "arxiv"

    def test_auto_skips_failing_engine(self):
        search = AcademicSearch()
        mock_fail = MagicMock()
        mock_fail._is_configured.return_value = True
        mock_fail.search.side_effect = RuntimeError("boom")

        mock_arxiv = MagicMock()
        mock_arxiv._is_configured.return_value = True
        mock_arxiv.search.return_value = [_make_paper(source="arxiv")]

        search._engine_cache["openalex"] = mock_fail
        search._engine_cache["arxiv"] = mock_arxiv

        results = search.search("test", engine="auto")
        assert len(results) == 1


class TestSearchSpecificEngine:
    def test_unknown_engine_raises(self):
        search = AcademicSearch()
        with pytest.raises(ValueError, match="Unknown"):
            search.search("test", engine="nonexistent")

    def test_specific_engine(self):
        search = AcademicSearch()
        mock_arxiv = MagicMock()
        mock_arxiv._is_configured.return_value = True
        mock_arxiv.search.return_value = [_make_paper(source="arxiv")]
        search._engine_cache["arxiv"] = mock_arxiv

        results = search.search("test", engine="arxiv")
        assert results[0].source == "arxiv"

    def test_unconfigured_without_fallback_raises(self):
        search = AcademicSearch()
        mock_engine = MagicMock()
        mock_engine._is_configured.return_value = False

        with (
            patch.object(search, "_get_engine", return_value=None),
            pytest.raises(RuntimeError, match="not configured"),
        ):
            search.search("test", engine="openalex")

    def test_unconfigured_with_fallback(self):
        search = AcademicSearch()
        mock_arxiv = MagicMock()
        mock_arxiv._is_configured.return_value = True
        mock_arxiv.search.return_value = [_make_paper(source="arxiv")]
        search._engine_cache["arxiv"] = mock_arxiv

        with patch.object(
            search,
            "_get_engine",
            side_effect=lambda n: None if n == "openalex" else mock_arxiv,
        ):
            results = search.search("test", engine="openalex", fallback=True)
            assert len(results) == 1


class TestEngineAnnotationNarrowing:
    def test_static_literal_includes_all(self):
        from toolregistry_hub.academics.academic_search import EngineName

        args = EngineName.__args__
        assert "auto" in args
        assert "openalex" in args
        assert "arxiv" in args

    def test_narrowed_when_engines_configured(self):
        search = AcademicSearch()
        annotations = (
            search.search.__func__.__annotations__
            if hasattr(search.search, "__func__")
            else search.search.__annotations__
        )
        engine_type = annotations.get("engine")
        if engine_type and hasattr(engine_type, "__args__"):
            assert "auto" in engine_type.__args__
