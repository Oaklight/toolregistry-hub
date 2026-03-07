"""Central tool registry for ToolRegistry Hub.

This module provides a centralized registry that registers all available tools
and automatically disables tools whose configuration is incomplete.

The registry supports two usage patterns:

1. **Server mode** (default): Relies on environment variables for configuration.
   Tools missing required env vars are auto-disabled.

2. **Custom configuration**: Pass ``tool_kwargs`` to ``build_registry()`` to
   provide API keys or other config directly, without environment variables.
"""

from typing import Dict, List, Optional, Tuple, Type

from loguru import logger
from toolregistry import ToolRegistry

from ..calculator import Calculator
from ..datetime_utils import DateTime
from ..fetch import Fetch
from ..file_ops import FileOps
from ..filesystem import FileSystem
from ..think_tool import ThinkTool
from ..todo_list import TodoList
from ..unit_converter import UnitConverter
from ..utils.configurable import Configurable
from ..utils.fn_namespace import _is_all_static_methods
from ..websearch import (
    BraveSearch,
    BrightDataSearch,
    ScrapelessSearch,
    SearXNGSearch,
    TavilySearch,
)

ALL_TOOLS: List[Tuple[Type, str]] = [
    (Calculator, "calculator"),
    (DateTime, "datetime"),
    (Fetch, "fetch"),
    (FileSystem, "filesystem"),
    (FileOps, "file_ops"),
    (ThinkTool, "think"),
    (TodoList, "todolist"),
    (UnitConverter, "unit_converter"),
    (BraveSearch, "brave_search"),
    (TavilySearch, "tavily_search"),
    (SearXNGSearch, "searxng_search"),
    (BrightDataSearch, "brightdata_search"),
    (ScrapelessSearch, "scrapeless_search"),
]


def build_registry(
    tool_kwargs: Optional[Dict[str, dict]] = None,
) -> ToolRegistry:
    """Build the hub tool registry with all tools registered and auto-disabled
    based on instance configuration state.

    Args:
        tool_kwargs: Optional mapping of namespace to constructor kwargs.
            Allows passing API keys or other config without env vars.
            Example: ``{"brave_search": {"api_keys": "my-key"}}``

    Returns:
        A fully configured ToolRegistry instance with all tools registered.
        Tools whose configuration is incomplete (as reported by the
        :class:`~toolregistry_hub.utils.Configurable` protocol) will be
        automatically disabled.
    """
    registry = ToolRegistry(name="hub")

    for cls, namespace in ALL_TOOLS:
        kwargs = (tool_kwargs or {}).get(namespace, {})

        if _is_all_static_methods(cls):
            registry.register_from_class(cls, with_namespace=namespace)
        else:
            instance = cls(**kwargs)
            registry.register_from_class(instance, with_namespace=namespace)

            # Check instance readiness via Configurable protocol
            if isinstance(instance, Configurable) and not instance.is_configured():
                required_envs: List[str] = getattr(cls, "_required_envs", [])
                reason = (
                    f"Missing env: {', '.join(required_envs)}"
                    if required_envs
                    else "Not configured"
                )
                for tool_name, tool in registry._tools.items():
                    if tool.namespace == namespace:
                        registry.disable(tool_name, reason=reason)
                logger.info(f"Disabled {namespace}: {reason}")

    return registry


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create the singleton hub tool registry.

    Returns:
        The singleton ToolRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry
