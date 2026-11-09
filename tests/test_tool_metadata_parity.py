"""Parity between the core decorator and the released-floor fallback.

The default test matrix installs the released core floor, where
``toolregistry_hub._metadata.tool_metadata`` stores a declaration and
``apply_declared_metadata`` applies it after registration.  The
``test-core-master`` job installs a core that applies the declaration in
``Tool.from_function``.  Every expectation here is the same under both.

The fallback is compared against the core in one run when the core has the
decorator: a declaration is stripped from a copy of the function, the
fallback is forced on, and the resulting metadata must equal the metadata
the core produced.
"""

from __future__ import annotations

import dataclasses
import types
from typing import Any

import pytest
from toolregistry import Tool, ToolMetadata, ToolRegistry

from toolregistry_hub import _metadata as md

#: Whether the installed core applies declarations itself.  Captured before
#: any test forces the fallback on.
CORE_APPLIES = md.CORE_APPLIES_DECLARATIONS

_PIPELINE_FIELDS = {
    "is_async",
    "source",
    "source_detail",
    "schema_hash",
    "last_refreshed_at",
}

_INSTALLED_FIELDS = {field.name for field in dataclasses.fields(ToolMetadata)}

#: A non-default value for every declarable field the installed core defines.
_SAMPLES: dict[str, Any] = {
    "is_concurrency_safe": False,
    "timeout": 30.0,
    "locality": "local",
    "max_result_size": 1024,
    "tags": {"read_only"},
    "custom_tags": {"team"},
    "extra": {"key": "value"},
    "defer": True,
    "search_hint": "find the thing",
    "think_augment": True,
    "natural_backend": "thread",
    "title": "Sample Tool",
    "read_only_hint": True,
    "destructive_hint": True,
    "idempotent_hint": True,
    "open_world_hint": True,
}

#: Every field a declaration may set on this core.
FIELDS = sorted((_INSTALLED_FIELDS - _PIPELINE_FIELDS) & set(_SAMPLES))


def _decorated(*layers: dict[str, Any]):
    """Build a sample tool, applying *layers* innermost first."""

    def sample() -> str:
        """Sample tool."""
        return "ok"

    for layer in layers:
        sample = md.tool_metadata(**layer)(sample)
    return sample


def _without_declaration(func: Any):
    """Return a copy of *func* that carries no declaration."""
    clone = types.FunctionType(
        func.__code__,
        func.__globals__,
        func.__name__,
        func.__defaults__,
        func.__closure__,
    )
    clone.__doc__ = func.__doc__
    clone.__kwdefaults__ = func.__kwdefaults__
    return clone


def _registered(func: Any, metadata: ToolMetadata | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    tool = Tool.from_function(func, metadata=metadata)
    registry._tools[tool.name] = tool
    return registry


def _fallback_metadata(
    monkeypatch: pytest.MonkeyPatch,
    func: Any,
    metadata: ToolMetadata | None = None,
) -> ToolMetadata:
    """Return the metadata the released-floor fallback produces.

    When the core applies declarations itself, the tool is built from a
    copy without one and the declaration is attached afterwards, so only
    the fallback can apply it.  On a released core the original function is
    used: the declaration lives only in its attribute.
    """
    declaration = getattr(func, md.DECLARED_ATTR, {})
    monkeypatch.setattr(md, "CORE_APPLIES_DECLARATIONS", False)
    target = _without_declaration(func) if CORE_APPLIES else func
    registry = _registered(target, metadata)
    name = next(iter(registry._tools))
    if CORE_APPLIES and declaration:
        setattr(registry._tools[name].fn, md.DECLARED_ATTR, dict(declaration))
    md.apply_declared_metadata(registry)
    return registry._tools[name].metadata


def _core_metadata(func: Any, metadata: ToolMetadata | None = None) -> ToolMetadata:
    """Return the metadata the installed core produces."""
    registry = _registered(func, metadata)
    return registry._tools[next(iter(registry._tools))].metadata


@pytest.mark.skipif(not FIELDS, reason="no declarable fields on this core")
class TestFieldParity:
    @pytest.mark.parametrize("field", FIELDS)
    def test_every_declarable_field(self, field: str, monkeypatch) -> None:
        func = _decorated({field: _SAMPLES[field]})

        fallback = _fallback_metadata(monkeypatch, func)
        assert getattr(fallback, field) == _SAMPLES[field]

        if CORE_APPLIES:
            core = _core_metadata(func)
            assert getattr(core, field) == _SAMPLES[field]
            assert core == fallback


class TestStacking:
    def test_outer_declaration_wins_in_both_paths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        func = _decorated({"title": "Inner", "defer": True}, {"title": "Outer"})

        fallback = _fallback_metadata(monkeypatch, func)
        assert fallback.title == "Outer"
        assert fallback.defer is True

        if CORE_APPLIES:
            core = _core_metadata(func)
            assert core.title == "Outer"
            assert core == fallback


class TestExplicitMetadata:
    def test_explicit_value_wins_in_both_paths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        func = _decorated({"tags": {"read_only"}, "defer": True})
        explicit = ToolMetadata(tags={"network"})

        fallback = _fallback_metadata(monkeypatch, func, explicit)
        assert fallback.tags == {"network"}
        assert fallback.defer is True

        if CORE_APPLIES:
            core = _core_metadata(func, explicit)
            assert core.tags == {"network"}
            assert core.defer is True
            assert core == fallback

    def test_explicit_tool_wins_over_the_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A value changed after registration is not overwritten."""
        func = _decorated({"title": "Declared"})
        if "title" not in _INSTALLED_FIELDS:
            pytest.skip("this core has no title field")
        monkeypatch.setattr(md, "CORE_APPLIES_DECLARATIONS", False)
        target = _without_declaration(func)
        setattr(target, md.DECLARED_ATTR, {"title": "Declared"})
        registry = _registered(target)
        name = next(iter(registry._tools))
        registry._replace_tool_metadata(name, title="Operator")
        md.apply_declared_metadata(registry)
        assert registry._tools[name].metadata.title == "Operator"


class TestFeatureDetection:
    def test_fallback_is_a_no_op_when_the_core_applies_declarations(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        if not CORE_APPLIES:
            pytest.skip("the installed core has no decorator")
        func = _decorated({"title": "Declared", "defer": True})
        registry = _registered(func)
        name = next(iter(registry._tools))
        before = registry._tools[name].metadata

        monkeypatch.setattr(md, "CORE_APPLIES_DECLARATIONS", False)
        md.apply_declared_metadata(registry)

        assert registry._tools[name].metadata == before


class TestSubmoduleReExport:
    """``BashTool`` is the one declaration not written on a Hub class member.

    It lives in the ``bashtool`` submodule and is attached from
    ``toolregistry_hub.bash_tool``; a change in that re-export would drop it
    silently.  The registration path below is the same one the server uses.
    """

    def test_bash_execute_keeps_its_declaration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from toolregistry.tool import ToolTag

        from toolregistry_hub.bash_tool import BashTool

        assert getattr(BashTool.execute, md.DECLARED_ATTR, None), (
            "the declaration is not on the function class registration re-uses"
        )

        registry = ToolRegistry()
        registry.register(BashTool, source="class", namespace="bash")
        monkeypatch.setattr(md, "CORE_APPLIES_DECLARATIONS", False)
        md.apply_declared_metadata(registry)

        tool = registry.get_tool("bash-execute")
        assert tool is not None
        metadata = tool.metadata
        assert metadata.defer is True
        assert ToolTag.DESTRUCTIVE in metadata.tags
        assert ToolTag.PRIVILEGED in metadata.tags
        if "title" in _INSTALLED_FIELDS:
            assert metadata.title == "Execute Shell Command"
