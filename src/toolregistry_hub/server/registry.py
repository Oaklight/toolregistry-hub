"""Central tool registry for ToolRegistry Hub.

This module provides a centralized registry that registers all available tools
and automatically disables tools whose configuration is incomplete.

Hub-specific concerns (content, not infrastructure):

- ``_DEFAULT_TOOLS``: built-in tool list as ``PythonSource`` entries
- ``_TOOL_METADATA``: namespace → tag/defer overrides applied post-registration
- ``configurable_hook``: post-register hook that auto-disables unconfigured tools

Deployment-context filtering (``--profile``) is handled by
``toolregistry-server >= 0.3.0`` and is not reimplemented here.
"""

import importlib

from toolregistry import ToolRegistry
from toolregistry.config import MCPSource, OpenAPISource, PythonSource, ToolConfig
from toolregistry.tool import ToolTag

from .._vendor.structlog import get_logger
from ..utils.configurable import Configurable
from ..utils.fn_namespace import _is_all_static_methods

logger = get_logger()

# Hub's built-in tool list expressed as PythonSource entries.
_DEFAULT_TOOLS: list[PythonSource] = [
    PythonSource(class_path="toolregistry_hub.bash_tool.BashTool", namespace="bash"),
    PythonSource(class_path="toolregistry_hub.cron_tool.CronTool", namespace="cron"),
    PythonSource(
        class_path="toolregistry_hub.calculator.Calculator", namespace="calculator"
    ),
    PythonSource(
        class_path="toolregistry_hub.datetime_utils.DateTime", namespace="datetime"
    ),
    PythonSource(class_path="toolregistry_hub.fetch.Fetch", namespace="web/fetch"),
    PythonSource(class_path="toolregistry_hub.file_ops.FileOps", namespace="file_ops"),
    PythonSource(
        class_path="toolregistry_hub.file_reader.FileReader", namespace="reader"
    ),
    PythonSource(
        class_path="toolregistry_hub.file_search.FileSearch",
        namespace="fs/file_search",
    ),
    PythonSource(
        class_path="toolregistry_hub.path_info.PathInfo", namespace="fs/path_info"
    ),
    PythonSource(class_path="toolregistry_hub.think_tool.ThinkTool", namespace="think"),
    PythonSource(
        class_path="toolregistry_hub.todo_list.TodoList", namespace="todolist"
    ),
    PythonSource(
        class_path="toolregistry_hub.unit_converter.UnitConverter",
        namespace="unit_converter",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_unified.WebSearch",
        namespace="web/websearch",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_brave.BraveSearch",
        namespace="web/brave_search",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_tavily.TavilySearch",
        namespace="web/tavily_search",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_searxng.SearXNGSearch",
        namespace="web/searxng_search",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_brightdata.BrightDataSearch",
        namespace="web/brightdata_search",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_scrapeless.ScrapelessSearch",
        namespace="web/scrapeless_search",
    ),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_serper.SerperSearch",
        namespace="web/serper_search",
    ),
]

# Metadata overrides for registered tools, keyed by namespace.
_TOOL_METADATA: dict[str, dict] = {
    "calculator": {"tags": {ToolTag.READ_ONLY}},
    "datetime": {"tags": {ToolTag.READ_ONLY}},
    "think": {"tags": {ToolTag.READ_ONLY}},
    "file_ops": {"tags": {ToolTag.FILE_SYSTEM, ToolTag.DESTRUCTIVE}},
    "web/fetch": {"tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
    "web/websearch": {"tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
    "web/brave_search": {"defer": True, "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
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
    "reader": {"defer": True, "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY}},
    "fs/file_search": {
        "defer": True,
        "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
    },
    "fs/path_info": {
        "defer": True,
        "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
    },
    "bash": {"defer": True, "tags": {ToolTag.DESTRUCTIVE, ToolTag.PRIVILEGED}},
    "cron": {"defer": True, "tags": {ToolTag.PRIVILEGED}},
    "todolist": {"defer": True, "tags": {ToolTag.READ_ONLY}},
    "unit_converter": {"defer": True, "tags": {ToolTag.READ_ONLY}},
}


def configurable_hook(name: str, tool: object, registry: ToolRegistry) -> str | None:
    """Post-registration hook: auto-disable tools that fail ``_is_configured()``.

    Args:
        name: The tool name just registered.
        tool: The ``Tool`` object (carries the bound instance via ``.callable.__self__``).
        registry: The registry the tool was added to.

    Returns:
        A disable reason string if the tool is not configured, else ``None``.
    """
    callable_ = getattr(tool, "callable", None)
    instance = getattr(callable_, "__self__", None)
    if instance is None:
        return None
    if isinstance(instance, Configurable) and not instance._is_configured():
        required_envs: list[str] = getattr(instance, "_required_envs", [])
        return (
            f"Missing env: {', '.join(required_envs)}"
            if required_envs
            else "Not configured"
        )
    return None


def _apply_tool_metadata(registry: ToolRegistry) -> None:
    """Apply tag and defer overrides from ``_TOOL_METADATA`` to all tools.

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


def _discover_config_path() -> str | None:
    """Auto-discover a tool config file path.

    Checks ``TOOLS_CONFIG`` env var, then ``tools.jsonc``, ``tools.yaml``,
    and ``tools.yml`` in the current directory.

    Returns:
        A file path string if a config file is found, else ``None``.
    """
    import os
    from pathlib import Path

    env_path = os.environ.get("TOOLS_CONFIG")
    if env_path and Path(env_path).is_file():
        return env_path
    for candidate in ("tools.jsonc", "tools.yaml", "tools.yml"):
        if Path(candidate).is_file():
            return candidate
    return None


def _merge_kwargs_into_source(
    src: PythonSource,
    tool_kwargs: dict[str, dict],
) -> PythonSource:
    """Return a copy of *src* with *tool_kwargs* merged in, or *src* unchanged.

    Args:
        src: The original ``PythonSource``.
        tool_kwargs: Namespace-tail → constructor kwargs map.

    Returns:
        A new ``PythonSource`` with merged kwargs, or the original if no match.
    """
    if not src.namespace:
        return src
    key = src.namespace.rsplit("/", 1)[-1]
    extra = tool_kwargs.get(key, {})
    if not extra:
        return src
    return PythonSource(
        class_path=src.class_path,
        namespace=src.namespace,
        kwargs=dict(extra),
    )


def _resolve_config(
    tools_config_path: str | None,
    tool_kwargs: dict[str, dict] | None,
) -> ToolConfig:
    """Load or build the tool config to register from.

    Priority: explicit path > ``toolregistry.config`` auto-discovery
    (``TOOLS_CONFIG`` env var / ``tools.jsonc``) > hub ``_DEFAULT_TOOLS``.

    Args:
        tools_config_path: Explicit config file path, or ``None``.
        tool_kwargs: Namespace-tail → constructor kwargs overrides.

    Returns:
        A ``ToolConfig`` ready for registration.
    """
    from toolregistry.config import load_config

    path = tools_config_path or _discover_config_path()
    config = load_config(path) if path else None

    if config is None or not config.tools:
        sources = [
            _merge_kwargs_into_source(src, tool_kwargs) if tool_kwargs else src
            for src in _DEFAULT_TOOLS
        ]
        return ToolConfig(tools=tuple(sources))

    # File config present — merge tool_kwargs into matching PythonSource entries
    if tool_kwargs:
        for src in config.tools:
            if isinstance(src, PythonSource) and src.namespace:
                key = src.namespace.rsplit("/", 1)[-1]
                extra = tool_kwargs.get(key, {})
                if extra:
                    src.kwargs.update(extra)

    return config


def _register_python_class_source(
    registry: ToolRegistry,
    source: PythonSource,
    _register_python_source_fn: object,
) -> None:
    """Register a single PythonSource with a ``class_path``.

    Handles three cases in order:
    1. Static-method-only class → register class directly (no hook).
    2. Class with constructor kwargs → instantiate with kwargs, then register.
    3. Otherwise → delegate to the server's ``_register_python_source`` helper.

    Args:
        registry: Destination registry.
        source: A ``PythonSource`` with a non-empty ``class_path``.
        _register_python_source_fn: The server helper function reference.
    """
    module_path, class_name = source.class_path.rsplit(".", 1)  # type: ignore[union-attr]
    cls = getattr(importlib.import_module(module_path), class_name)
    ns: bool | str = source.namespace or False

    if _is_all_static_methods(cls):
        registry.register_from_class(cls, namespace=ns)
        return

    if source.kwargs:
        # Server helper ignores source.kwargs; instantiate ourselves so that
        # Configurable checks in the post-register hook see the right state.
        instance = cls(**source.kwargs)
        registry.register_from_class(instance, namespace=ns)
        logger.info(f"Loaded class tools from {source.class_path}")
        return

    _register_python_source_fn(registry, source)  # type: ignore[operator]


def _register_sources(registry: ToolRegistry, config: ToolConfig) -> None:
    """Register all enabled sources from *config* into *registry*.

    Args:
        registry: Destination registry (hooks must be attached beforehand).
        config: Tool config whose sources to register.
    """
    from toolregistry_server.cli.openapi import (
        _register_mcp_source,
        _register_openapi_source,
        _register_python_source,
    )

    for source in config.tools:
        if not source.enabled:
            continue
        try:
            if isinstance(source, PythonSource) and source.class_path:
                _register_python_class_source(registry, source, _register_python_source)
            elif isinstance(source, PythonSource):
                _register_python_source(registry, source)
            elif isinstance(source, MCPSource):
                _register_mcp_source(registry, source)
            elif isinstance(source, OpenAPISource):
                _register_openapi_source(registry, source)
        except Exception as e:
            logger.warning(f"Failed to load tool source {source}: {e}")


def build_registry(
    tool_kwargs: dict[str, dict] | None = None,
    tools_config_path: str | None = None,
    enable_discovery: bool = True,
    enable_think: bool = True,
) -> ToolRegistry:
    """Build the hub tool registry.

    Args:
        tool_kwargs: Namespace-tail → constructor kwargs.
            Example: ``{"brave_search": {"api_keys": "my-key"}}``
        tools_config_path: Path to a JSONC/YAML config file, or ``None`` for
            auto-discovery (``TOOLS_CONFIG`` env var / ``tools.jsonc``).
        enable_discovery: Register ``discover_tools`` and mark deferred tools.
        enable_think: Inject ``toolcall_reason`` into tool schemas.

    Returns:
        A fully configured ``ToolRegistry`` instance.
    """
    config = _resolve_config(tools_config_path, tool_kwargs)

    registry = ToolRegistry(name="hub", think_augment=enable_think)
    registry.add_post_register_hook(configurable_hook)

    _register_sources(registry, config)
    _apply_tool_metadata(registry)

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
