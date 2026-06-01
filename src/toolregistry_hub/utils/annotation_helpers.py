"""Helpers for runtime manipulation of function type annotations.

These utilities exist primarily to control how tool input schemas are
generated for MCP / LLM clients. When a parameter's set of valid values is
known only at runtime (e.g. the registry of unit-conversion function names,
or the set of configured search engines), we want the JSON schema to expose
those values as an ``enum`` instead of an unconstrained ``string``. The
cleanest way to achieve that with the upstream ``toolregistry`` / pydantic
stack is to rewrite the function's ``__annotations__`` so that the parameter
is typed as ``Literal[...]``.
"""

from __future__ import annotations

import types
from collections.abc import Callable, Iterable
from typing import Any, Literal


def bind_literal(
    func: types.FunctionType | Callable[..., Any],
    param: str,
    choices: Iterable[Any],
    *,
    instance: object | None = None,
) -> Callable[..., Any]:
    """Return a copy of ``func`` whose ``param`` annotation is ``Literal[*choices]``.

    The original function is not modified; the returned callable has its own
    ``__annotations__`` dict so further mutations are isolated.

    Args:
        func: The function (or unbound method) to copy. Must be a regular
            Python function object — built-in callables and arbitrary
            ``__call__`` objects are not supported because we need to inspect
            their ``__code__`` / ``__globals__``.
        param: Name of the parameter whose annotation should be replaced.
        choices: Iterable of values to include in the ``Literal``. Must be
            non-empty and contain hashable, ``Literal``-compatible values
            (typically strings).
        instance: When ``func`` is an unbound method and the caller wants the
            result re-bound as a method, pass the owning instance here. The
            returned object will then be a ``types.MethodType`` bound to
            ``instance``. When ``None`` (default), a plain function is
            returned.

    Returns:
        A new function (or bound method, if ``instance`` is given) whose
        ``__annotations__[param]`` is set to a fresh ``Literal`` built from
        ``choices``.

    Raises:
        TypeError: If ``func`` is not a regular Python function.
        ValueError: If ``choices`` is empty, or if ``param`` is not present
            in the function's annotations.

    Example:
        >>> def search(engine: str = "auto") -> None: ...
        >>> narrowed = bind_literal(search, "engine", ["auto", "brave", "tavily"])
        >>> narrowed.__annotations__["engine"]
        typing.Literal['auto', 'brave', 'tavily']
    """
    choice_tuple = tuple(choices)
    if not choice_tuple:
        raise ValueError("choices must be non-empty")

    # ``func`` must be a regular function object so we can reach its code /
    # globals; narrow the static type here so attribute lookups below resolve.
    if not isinstance(func, types.FunctionType):
        raise TypeError(
            f"bind_literal requires a Python function, got {type(func).__name__}"
        )

    original_annotations = dict(func.__annotations__ or {})
    if param not in original_annotations:
        raise ValueError(
            f"Parameter {param!r} is not annotated on {func.__qualname__}; "
            f"available annotated params: {sorted(original_annotations)}"
        )

    new_func = types.FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=func.__defaults__,
        closure=func.__closure__,
    )
    new_func.__doc__ = func.__doc__
    new_func.__qualname__ = func.__qualname__
    new_func.__module__ = func.__module__
    new_func.__kwdefaults__ = func.__kwdefaults__
    new_func.__annotations__ = original_annotations
    # ``Literal[...]`` requires subscripting with either a single value or a
    # tuple, so dispatch through ``__getitem__`` directly to accept the
    # runtime-built tuple.
    new_func.__annotations__[param] = Literal.__getitem__(choice_tuple)

    if instance is not None:
        return types.MethodType(new_func, instance)
    return new_func
