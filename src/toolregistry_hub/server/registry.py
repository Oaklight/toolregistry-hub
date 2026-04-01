"""Central tool registry for ToolRegistry Hub.

This module provides a centralized registry that registers all available tools
and automatically disables tools whose configuration is incomplete.

The registry supports two usage patterns:

1. **Server mode** (default): Relies on environment variables for configuration.
   Tools missing required env vars are auto-disabled.

2. **Custom configuration**: Pass ``tool_kwargs`` to ``build_registry()`` to
   provide API keys or other config directly, without environment variables.
"""

import importlib

from loguru import logger
from toolregistry import ToolRegistry

from ..utils.configurable import Configurable
from ..utils.fn_namespace import _is_all_static_methods

_DEFAULT_TOOLS: list[dict[str, str]] = [
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "datetime"},
    {"class": "toolregistry_hub.fetch.Fetch", "namespace": "web/fetch"},
    {"class": "toolregistry_hub.filesystem.FileSystem", "namespace": "filesystem"},
    {"class": "toolregistry_hub.file_ops.FileOps", "namespace": "file_ops"},
    {"class": "toolregistry_hub.path_info.PathInfo", "namespace": "fs/path_info"},
    {"class": "toolregistry_hub.think_tool.ThinkTool", "namespace": "think"},
    {"class": "toolregistry_hub.todo_list.TodoList", "namespace": "todolist"},
    {
        "class": "toolregistry_hub.unit_converter.UnitConverter",
        "namespace": "unit_converter",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_brave.BraveSearch",
        "namespace": "web/brave_search",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_tavily.TavilySearch",
        "namespace": "web/tavily_search",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_searxng.SearXNGSearch",
        "namespace": "web/searxng_search",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch",
        "namespace": "web/brightdata_search",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_scrapeless.ScrapelessSearch",
        "namespace": "web/scrapeless_search",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_serper.SerperSearch",
        "namespace": "web/serper_search",
    },
]

# Methods to exclude from route generation (internal/protocol methods)
# Note: Methods starting with "_" are already excluded by toolregistry,
# but we keep this for any other internal methods that need hiding.
_HIDDEN_METHODS: set[str] = set()


def _import_class(class_path: str) -> type:
    """Dynamically import a class from a dotted path string.

    Args:
        class_path: Fully qualified class path,
            e.g. ``"toolregistry_hub.calculator.Calculator"``.

    Returns:
        The imported class object.

    Raises:
        ImportError: If the module cannot be imported.
        AttributeError: If the class is not found in the module.
    """
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def build_registry(
    tool_kwargs: dict[str, dict] | None = None,
    tools_config_path: str | None = None,
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

    # Load config early so we can read the tools list from it
    config = load_tool_config(tools_config_path)

    # Determine tool list: config file > default
    tool_entries = config.tools if (config and config.tools is not None) else None
    if tool_entries is not None:
        tools_to_register = [
            {"class": e.class_path, "namespace": e.namespace} for e in tool_entries
        ]
    else:
        tools_to_register = _DEFAULT_TOOLS

    registry = ToolRegistry(name="hub")

    for tool_def in tools_to_register:
        class_path = tool_def["class"]
        namespace = tool_def["namespace"]

        try:
            cls = _import_class(class_path)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import tool class '{class_path}': {e}")
            continue

        # For tool_kwargs lookup, use the leaf namespace (after last '/')
        kwargs_key = namespace.rsplit("/", 1)[-1]
        kwargs = (tool_kwargs or {}).get(kwargs_key, {})

        if _is_all_static_methods(cls):
            registry.register_from_class(cls, with_namespace=namespace)
        else:
            instance = cls(**kwargs)
            registry.register_from_class(instance, with_namespace=namespace)

            # Check instance readiness via Configurable protocol
            if isinstance(instance, Configurable) and not instance._is_configured():
                required_envs: list[str] = getattr(cls, "_required_envs", [])
                reason = (
                    f"Missing env: {', '.join(required_envs)}"
                    if required_envs
                    else "Not configured"
                )
                for tool_name, tool in registry._tools.items():
                    if tool.namespace == namespace:
                        registry.disable(tool_name, reason=reason)
                logger.info(f"Disabled {namespace}: {reason}")

    # Remove hidden methods from the registry (if any are explicitly listed)
    # Note: Methods starting with "_" are already excluded by toolregistry
    if _HIDDEN_METHODS:
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
    if config is not None:
        apply_tool_config(registry, config)

    return registry


_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get or create the singleton hub tool registry.

    Returns:
        The singleton ToolRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry
