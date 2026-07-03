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

from toolregistry import ToolRegistry
from toolregistry.config import PythonSource, ToolConfig
from toolregistry.tool import ToolTag

from .._vendor.structlog import get_logger
from ..utils.configurable import Configurable

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
    PythonSource(class_path="toolregistry_hub.weather.Weather", namespace="weather"),
    PythonSource(
        class_path="toolregistry_hub.websearch.websearch_unified.WebSearch",
        namespace="web/websearch",
    ),
]

# Metadata overrides for registered tools, keyed by namespace.
_TOOL_METADATA: dict[str, dict] = {
    "calculator": {"defer": True, "tags": {ToolTag.READ_ONLY}},
    "datetime": {
        "tags": {ToolTag.READ_ONLY},
        "methods": {
            "convert_timezone": {"defer": True},
        },
    },
    "think": {"tags": {ToolTag.READ_ONLY}},
    "file_ops": {"tags": {ToolTag.FILE_SYSTEM, ToolTag.DESTRUCTIVE}},
    "web/fetch": {"tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
    "web/websearch": {
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
        "methods": {
            "list_engines": {"defer": True},
        },
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
    "weather": {"defer": True, "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY}},
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


def _apply_overrides(tool: object, overrides: dict) -> None:
    """Apply a single overrides dict to a tool's metadata.

    Supported keys: ``defer``, ``tags``, ``search_hint``.

    Args:
        tool: A ``Tool`` instance (duck-typed via ``.metadata``).
        overrides: Dict with optional ``defer``, ``tags``, and/or
            ``search_hint`` keys.
    """
    meta = getattr(tool, "metadata", None)
    if meta is None:
        return
    if "defer" in overrides:
        meta.defer = overrides["defer"]
    if "tags" in overrides:
        meta.tags = overrides["tags"]
    if "search_hint" in overrides:
        meta.search_hint = overrides["search_hint"]


def _apply_tool_metadata(registry: ToolRegistry) -> None:
    """Apply tag and defer overrides from ``_TOOL_METADATA`` to all tools.

    Namespace-level overrides are applied first; method-level overrides
    (nested under the ``methods`` key) are applied afterwards and take
    precedence for the matched tool.  Method lookup is by
    ``tool.method_name`` so it is independent of the name separator.

    Example ``_TOOL_METADATA`` entry with method-level override::

        "calculator": {
            "tags": {ToolTag.READ_ONLY},
            "methods": {
                "evaluate": {"defer": True},
            },
        }

    Args:
        registry: The registry whose tools should be annotated.
    """
    for tool in registry._tools.values():
        ns = tool.namespace
        if not ns or ns not in _TOOL_METADATA:
            continue
        ns_meta = _TOOL_METADATA[ns]
        _apply_overrides(tool, ns_meta)
        # Method-level override — keyed by method_name, separator-independent
        method_overrides: dict[str, dict] = ns_meta.get("methods", {})
        if (
            method_overrides
            and tool.method_name
            and tool.method_name in method_overrides
        ):
            _apply_overrides(tool, method_overrides[tool.method_name])


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


def _resolve_config(
    tools_config_path: str | None = None,
) -> ToolConfig:
    """Load or build the tool config to register from.

    Priority: explicit path > auto-discovery
    (``TOOLS_CONFIG`` env var / ``tools.jsonc``) > hub ``_DEFAULT_TOOLS``.

    Args:
        tools_config_path: Explicit config file path, or ``None``.

    Returns:
        A ``ToolConfig`` ready for registration.
    """
    from toolregistry_server import load_config

    path = tools_config_path or _discover_config_path()
    config = load_config(path) if path is not None else None

    if config is None or not config.tools:
        return ToolConfig(tools=tuple(_DEFAULT_TOOLS))

    return config


def build_registry(
    tools_config_path: str | None = None,
    enable_discovery: bool = True,
    enable_think: bool = True,
) -> ToolRegistry:
    """Build the hub tool registry.

    Two-phase construction:

    1. Register built-in tools from ``_DEFAULT_TOOLS`` (or a user config
       file if provided) via ``toolregistry_server.apply_config``.
    2. Apply Hub-specific metadata overrides (tags, defer).

    Args:
        tools_config_path: Path to a JSONC/YAML config file, or ``None`` for
            auto-discovery (``TOOLS_CONFIG`` env var / ``tools.jsonc``).
        enable_discovery: Register ``discover_tools`` and mark deferred tools.
        enable_think: Inject ``toolcall_reason`` into tool schemas.

    Returns:
        A fully configured ``ToolRegistry`` instance.
    """
    from toolregistry_server import apply_config

    config = _resolve_config(tools_config_path)

    registry = ToolRegistry(name="hub", think_augment=enable_think)
    registry.add_post_register_hook(configurable_hook)

    # Register tools from config (built-in defaults or user override)
    apply_config(registry, config)

    # Hub-specific metadata overrides (tags, defer)
    _apply_tool_metadata(registry)

    # Re-apply user config overrides so they take precedence over hub defaults
    if config.tool_metadata:
        registry.apply_metadata_config(config.tool_metadata)

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
