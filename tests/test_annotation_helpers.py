"""Tests for ``toolregistry_hub.utils.annotation_helpers``."""

from __future__ import annotations

from typing import Literal, get_type_hints

import pytest

from toolregistry_hub.utils import bind_literal


def _example(engine: str = "auto", count: int = 1) -> str:
    """Example function with a string parameter that should be narrowed."""
    return f"{engine}:{count}"


class TestBindLiteral:
    def test_replaces_annotation_with_literal(self):
        narrowed = bind_literal(_example, "engine", ["auto", "brave", "tavily"])
        # The new function's raw annotation should be a Literal of the choices.
        ann = narrowed.__annotations__["engine"]
        assert ann == Literal["auto", "brave", "tavily"]

    def test_get_type_hints_sees_literal(self):
        """``get_type_hints`` is what pydantic / toolregistry use for schema."""
        narrowed = bind_literal(_example, "engine", ("auto", "brave"))
        hints = get_type_hints(narrowed)
        assert hints["engine"] == Literal["auto", "brave"]

    def test_original_function_untouched(self):
        original_ann = dict(_example.__annotations__)
        bind_literal(_example, "engine", ["auto"])
        assert _example.__annotations__ == original_ann

    def test_call_still_works(self):
        narrowed = bind_literal(_example, "engine", ["auto", "x"])
        # Runtime call semantics are unchanged; Literal is a static-only hint.
        assert narrowed("x", 2) == "x:2"

    def test_preserves_other_annotations_and_defaults(self):
        narrowed = bind_literal(_example, "engine", ["auto"])
        hints = get_type_hints(narrowed)
        assert hints["count"] is int
        assert narrowed() == "auto:1"  # defaults still intact

    def test_empty_choices_rejected(self):
        with pytest.raises(ValueError, match="choices must be non-empty"):
            bind_literal(_example, "engine", [])

    def test_unknown_param_rejected(self):
        with pytest.raises(ValueError, match="not annotated"):
            bind_literal(_example, "nonexistent", ["a"])

    def test_non_function_rejected(self):
        with pytest.raises(TypeError, match="requires a Python function"):
            bind_literal(len, "x", ["a"])  # type: ignore[arg-type]

    def test_instance_kwarg_returns_bound_method(self):
        class Holder:
            def search(self, engine: str = "auto") -> str:
                return f"{type(self).__name__}:{engine}"

        h = Holder()
        bound = bind_literal(Holder.search, "engine", ["auto", "x"], instance=h)
        # When instance is given, we get a bound method
        assert bound.__self__ is h  # type: ignore[attr-defined]
        assert bound("x") == "Holder:x"
