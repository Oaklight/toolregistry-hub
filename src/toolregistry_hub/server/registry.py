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
    (BraveSearch, "web/brave_search"),
    (TavilySearch, "web/tavily_search"),
    (SearXNGSearch, "web/searxng_search"),
    (BrightDataSearch, "web/brightdata_search"),
    (ScrapelessSearch, "web/scrapeless_search"),
]

# Methods to exclude from route generation (internal/protocol methods)
_HIDDEN_METHODS: set[str] = {"is_configured"}


def build_registry(
    tool_kwargs: Optional[Dict[str, dict]] = None,
    tools_config_path: Optional[str] = None,
) -> ToolRegistry:
    """Build the hub tool registry with all tools registered and auto-disabled
    based on instance configuration state.

    Args:
        tool_kwargs: Optional mapping of namespace to constructor kwargs.
            Allows passing API keys or other config without env vars.
            Example: ``{"brave_search": {"api_keys": "my-key"}}``
        tools_config_path: Optional path to a JSONC tool configuration file.
            If ``None``, the default discovery order is used (env var, then
            ``./tools.jsonc``).

    Returns:
        A fully configured ToolRegistry instance with all tools registered.
        Tools whose configuration is incomplete (as reported by the
        :class:`~toolregistry_hub.utils.Configurable` protocol) will be
        automatically disabled.  Additional disable/enable rules from the
        tool configuration file are applied afterwards.
    """
    from .tool_config import apply_tool_config, load_tool_config

    registry = ToolRegistry(name="hub")

    for cls, namespace in ALL_TOOLS:
        # For tool_kwargs lookup, use the leaf namespace (after last '/')
        kwargs_key = namespace.rsplit("/", 1)[-1]
        kwargs = (tool_kwargs or {}).get(kwargs_key, {})

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

    # Remove hidden methods (e.g. is_configured) from the registry
    to_remove = [
        name
        for name, tool in registry._tools.items()
        if tool.method_name in _HIDDEN_METHODS
    ]
    for name in to_remove:
        del registry._tools[name]
        registry._disabled.pop(name, None)
        logger.debug(f"Removed hidden method from registry: {name}")

    # Apply startup tool configuration (highest priority)
    config = load_tool_config(tools_config_path)
    if config is not None:
        apply_tool_config(registry, config)

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
