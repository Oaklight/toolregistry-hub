"""Tool metadata declarations and the released-floor fallback.

``@tool_metadata`` ships with toolregistry 0.21.0.  Hub supports an older
core floor, so this module re-exports the core decorator when it is
importable and otherwise stores the same ``__tool_metadata__`` attribute on
the function.  ``Tool.from_function`` applies a declaration on a core that
has the decorator; on an older core :func:`apply_declared_metadata` applies
the same rule after registration.

Only the declaration channel lives here.  A tool module decorates its own
methods, so class registration carries the metadata without a namespace
table or a per-source replay.

The fallback is deleted when the dependency floor reaches a core release
that provides the decorator.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Set
from typing import Any, TypeVar

from toolregistry import ToolRegistry
from toolregistry.tool import ToolMetadata

#: Attribute the core decorator stores a declaration under.
DECLARED_ATTR = "__tool_metadata__"

#: Metadata fields the registration pipeline owns; a declaration never sets
#: them, matching the core decorator's rule.
_PIPELINE_FIELDS = frozenset(
    {"is_async", "source", "source_detail", "schema_hash", "last_refreshed_at"}
)

try:  # toolregistry >= 0.21.0
    from toolregistry import tool_metadata

    CORE_APPLIES_DECLARATIONS = True
    """Whether the installed core applies ``__tool_metadata__`` itself."""
except ImportError:  # pragma: no cover - exercised on the released floor
    CORE_APPLIES_DECLARATIONS = False

    _F = TypeVar("_F", bound=Callable[..., Any])

    def tool_metadata(**fields: Any) -> Callable[[_F], _F]:
        """Store a declaration where the core decorator stores it.

        Deliberately dumb: it validates and fills nothing, so the released
        floor cannot drift from the core in how a declaration is stored.
        Stacking keeps the outer declaration, as the core decorator does.

        Args:
            **fields: Metadata values to store on the decorated function.

        Returns:
            A decorator that stores the values and returns the function.
        """
        declared = dict(fields)

        def decorator(func: _F) -> _F:
            existing = getattr(func, DECLARED_ATTR, None)
            setattr(func, DECLARED_ATTR, {**(existing or {}), **declared})
            return func

        return decorator


def _field_default(field: dataclasses.Field[Any]) -> Any:
    """Return the default value a dataclass field would take."""
    if field.default is not dataclasses.MISSING:
        return field.default
    factory = field.default_factory
    if factory is dataclasses.MISSING:
        raise RuntimeError(f"field {field.name!r} has no default")
    return factory()


#: Default of every field the installed :class:`ToolMetadata` defines.
_DEFAULTS: dict[str, Any] = {
    field.name: _field_default(field) for field in dataclasses.fields(ToolMetadata)
}

#: Fields the installed core accepts from a declaration.
_DECLARABLE: frozenset[str] = frozenset(_DEFAULTS) - _PIPELINE_FIELDS


def declared_metadata(func: Any) -> dict[str, Any]:
    """Return the declaration stored on *func*, limited to usable fields.

    Args:
        func: The function a tool was built from.

    Returns:
        The declared values whose names the installed core defines.
    """
    declared = getattr(func, DECLARED_ATTR, None)
    if not isinstance(declared, dict):
        return {}
    return {name: value for name, value in declared.items() if name in _DECLARABLE}


def apply_declared_metadata(
    registry: ToolRegistry, names: Set[str] | None = None
) -> None:
    """Apply declarations the installed core did not apply.

    Mirrors ``Tool.from_function``: a field still at its dataclass default
    is filled from the declaration, so a value supplied explicitly (by the
    config file or the admin panel) always wins.  This is a no-op on a core
    that applies declarations itself.

    Args:
        registry: The registry whose tools should be annotated.
        names: When given, annotate only these tools.  A hot reload passes
            the names it registered, so a tool that already existed keeps a
            value an operator changed.
    """
    if CORE_APPLIES_DECLARATIONS:
        return
    updates: list[tuple[str, dict[str, Any]]] = []
    for tool in registry._tools.values():
        if names is not None and tool.name not in names:
            continue
        declared = declared_metadata(tool.fn)
        if not declared:
            continue
        current = tool.metadata
        fill = {
            name: value
            for name, value in declared.items()
            if getattr(current, name) == _DEFAULTS[name]
        }
        if fill:
            updates.append((tool.name, fill))
    for name, fill in updates:
        registry._replace_tool_metadata(name, **fill)


__all__ = [
    "CORE_APPLIES_DECLARATIONS",
    "DECLARED_ATTR",
    "apply_declared_metadata",
    "declared_metadata",
    "tool_metadata",
]
