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

from toolregistry import ToolRegistry
from toolregistry.tool import ToolTag

from .._vendor.structlog import get_logger
from ..utils.configurable import Configurable
from ..utils.fn_namespace import _is_all_static_methods

logger = get_logger()

_DEFAULT_TOOLS: list[dict[str, str]] = [
    {"class": "toolregistry_hub.bash_tool.BashTool", "namespace": "bash"},
    {"class": "toolregistry_hub.cron_tool.CronTool", "namespace": "cron"},
    {"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"},
    {"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "datetime"},
    {"class": "toolregistry_hub.fetch.Fetch", "namespace": "web/fetch"},
    {"class": "toolregistry_hub.file_ops.FileOps", "namespace": "file_ops"},
    {"class": "toolregistry_hub.file_reader.FileReader", "namespace": "reader"},
    {"class": "toolregistry_hub.file_search.FileSearch", "namespace": "fs/file_search"},
    {"class": "toolregistry_hub.path_info.PathInfo", "namespace": "fs/path_info"},
    {"class": "toolregistry_hub.think_tool.ThinkTool", "namespace": "think"},
    {"class": "toolregistry_hub.todo_list.TodoList", "namespace": "todolist"},
    {
        "class": "toolregistry_hub.unit_converter.UnitConverter",
        "namespace": "unit_converter",
    },
    {
        "class": "toolregistry_hub.websearch.websearch_unified.WebSearch",
        "namespace": "web/websearch",
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

# Metadata overrides for registered tools, keyed by namespace.
# Sets ToolTag and defer flags after register_from_class().
_TOOL_METADATA: dict[str, dict] = {
    # Core tools (always visible in initial schema)
    "calculator": {"tags": {ToolTag.READ_ONLY}},
    "datetime": {"tags": {ToolTag.READ_ONLY}},
    "think": {"tags": {ToolTag.READ_ONLY}},
    "file_ops": {"tags": {ToolTag.FILE_SYSTEM, ToolTag.DESTRUCTIVE}},
    "web/fetch": {"tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
    # Unified websearch entry (visible by default)
    "web/websearch": {"tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
    # Provider-specific search engines (deferred — discoverable via discover_tools)
    "web/brave_search": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
    },
    "web/tavily_search": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
    },
    "web/searxng_search": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
    },
    "web/brightdata_search": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
    },
    "web/scrapeless_search": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
    },
    "web/serper_search": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
    },
    # Deferred tools (discoverable via discover_tools)
    "reader": {"defer": True, "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY}},
    "fs/file_search": {"defer": True, "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY}},
    "fs/path_info": {"defer": True, "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY}},
    "bash": {"defer": True, "tags": {ToolTag.DESTRUCTIVE, ToolTag.PRIVILEGED}},
    "cron": {"defer": True, "tags": {ToolTag.PRIVILEGED}},
    "todolist": {"defer": True, "tags": {ToolTag.READ_ONLY}},
    "unit_converter": {"defer": True, "tags": {ToolTag.READ_ONLY}},
}


def _apply_tool_metadata(registry: ToolRegistry) -> None:
    """Apply tags, defer flags, and search hints to registered tools.

    Iterates all tools in the registry and applies metadata overrides
    from ``_TOOL_METADATA`` based on each tool's namespace.

    Args:
        registry: The registry whose tools should be annotated.
    """
    for tool in registry._tools.values():
        ns = tool.namespace
        if ns and ns in _TOOL_METADATA:
            overrides = _TOOL_METADATA[ns]
            if "defer" in overrides:
                tool.metadata.defer = overrides["defer"]
            if "tags" in overrides:
                tool.metadata.tags = overrides["tags"]
            if "search_hint" in overrides:
                tool.metadata.search_hint = overrides["search_hint"]


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


def _register_tool(
    registry: ToolRegistry,
    class_path: str,
    namespace: str,
    kwargs: dict,
) -> None:
    """Import, instantiate, and register a single tool class.

    Static-method-only classes are registered directly; others are
    instantiated first.  Instances that implement the
    :class:`~toolregistry_hub.utils.Configurable` protocol are checked
    for readiness, and all tools under their namespace are auto-disabled
    when configuration is incomplete.

    Args:
        registry: The registry to add the tool to.
        class_path: Fully qualified class path to import.
        namespace: Namespace under which to register.
        kwargs: Constructor keyword arguments for the tool class.
    """
    try:
        cls = _import_class(class_path)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import tool class '{class_path}': {e}")
        return

    if _is_all_static_methods(cls):
        registry.register_from_class(cls, namespace=namespace)
        return

    instance = cls(**kwargs)
    registry.register_from_class(instance, namespace=namespace)

    if isinstance(instance, Configurable) and not instance._is_configured():
        _disable_namespace(registry, cls, namespace)


def _disable_namespace(registry: ToolRegistry, cls: type, namespace: str) -> None:
    """Disable all tools under *namespace* due to missing configuration.

    Args:
        registry: The registry containing the tools.
        cls: The tool class (used to read ``_required_envs``).
        namespace: Namespace whose tools should be disabled.
    """
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


def _remove_hidden_methods(registry: ToolRegistry) -> None:
    """Remove explicitly hidden methods from the registry.

    Note: Methods starting with ``_`` are already excluded by toolregistry;
    this handles any additional methods listed in ``_HIDDEN_METHODS``.

    Args:
        registry: The registry to clean up.
    """
    if not _HIDDEN_METHODS:
        return
    to_remove = [
        name
        for name, tool in registry._tools.items()
        if tool.method_name in _HIDDEN_METHODS
    ]
    for name in to_remove:
        del registry._tools[name]
        registry._disabled.pop(name, None)
        logger.debug(f"Removed hidden method from registry: {name}")


def build_registry(
    tool_kwargs: dict[str, dict] | None = None,
    tools_config_path: str | None = None,
    enable_discovery: bool = True,
    enable_think: bool = True,
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
        enable_discovery: Enable tool discovery (progressive disclosure).
            When ``True``, registers a ``discover_tools`` tool and marks
            selected tools as deferred.
        enable_think: Enable think-augmented function calling.
            When ``True``, injects a ``thought`` property into tool schemas
            for chain-of-thought reasoning.

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

    registry = ToolRegistry(name="hub", think_augment=enable_think)

    for tool_def in tools_to_register:
        namespace = tool_def["namespace"]
        kwargs_key = namespace.rsplit("/", 1)[-1]
        kwargs = (tool_kwargs or {}).get(kwargs_key, {})
        _register_tool(registry, tool_def["class"], namespace, kwargs)

    _remove_hidden_methods(registry)

    # Apply startup tool configuration (highest priority)
    if config is not None:
        apply_tool_config(registry, config)

    # Apply metadata (tags, defer flags) to registered tools
    _apply_tool_metadata(registry)

    # Enable tool discovery (registers discover_tools, indexes all tools)
    if enable_discovery:
        registry.enable_tool_discovery()

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
