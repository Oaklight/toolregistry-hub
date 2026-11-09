"""Central tool registry for ToolRegistry Hub.

This module provides a centralized registry that registers all available tools
and automatically disables tools whose configuration is incomplete.

Hub-specific concerns (content, not infrastructure):

- ``_DEFAULT_TOOLS``: built-in tool list as ``PythonSource`` entries
- ``@tool_metadata``: tag/defer/hint declarations on the tool methods;
  applied by the core, with a released-floor fallback in ``_metadata``
- ``output_schemas.OUTPUT_SCHEMAS``: declared result shapes, published as
  MCP ``outputSchema`` / ``structuredContent``
- ``configurable_hook``: post-register hook that auto-disables unconfigured tools

Deployment-context filtering (``--profile``) is handled by
``toolregistry-server >= 0.3.0`` and is not reimplemented here.
"""

from __future__ import annotations

from collections.abc import Set
from dataclasses import fields as dataclass_fields
from typing import Any

from toolregistry import ToolRegistry
from toolregistry.config import PythonSource, ToolConfig
from toolregistry.tool import ToolMetadata

from .._metadata import apply_declared_metadata
from .._vendor.structlog import get_logger
from ..utils.configurable import Configurable
from .hot_reload import ReloadState, apply_config_tracked, index_sources
from .output_schemas import OUTPUT_SCHEMAS

logger = get_logger()

# Fields the installed toolregistry accepts on ToolMetadata.  Execution
# hints and ``title`` were added after some supported releases, and Hub can
# be installed against an older core (it is pulled in through
# toolregistry-server).  Overrides for unknown fields are skipped instead
# of raising in ``dataclasses.replace``; annotations then simply stay
# absent until the core is upgraded.
_METADATA_FIELDS: frozenset[str] = frozenset(
    f.name for f in dataclass_fields(ToolMetadata)
)

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
    PythonSource(class_path="toolregistry_hub.fetch.Fetch", namespace="web"),
    PythonSource(class_path="toolregistry_hub.file_ops.FileOps", namespace="file_ops"),
    PythonSource(
        class_path="toolregistry_hub.file_reader.FileReader", namespace="reader"
    ),
    PythonSource(
        class_path="toolregistry_hub.file_search.FileSearch",
        namespace="fs",
    ),
    PythonSource(class_path="toolregistry_hub.path_info.PathInfo", namespace="fs"),
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
        namespace="web",
    ),
    PythonSource(
        class_path="toolregistry_hub.academics.academic_search.AcademicSearch",
        namespace="academics",
    ),
]


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


def _output_schema_update(namespace: str, tool: Any) -> dict:
    """Return the ``extra`` metadata update carrying a declared result schema.

    A declared schema lives in ``ToolMetadata.extra["output_schema"]`` because
    that is where ``toolregistry-server`` reads it.  Merge rather than replace:
    another integration may already have written keys there.

    Args:
        namespace: The tool's namespace.
        tool: The registered tool.

    Returns:
        A dict with an ``extra`` key, or an empty dict when this tool declares
        no schema or the installed core has no ``extra`` field.
    """
    if "extra" not in _METADATA_FIELDS:
        return {}
    schema = OUTPUT_SCHEMAS.get(namespace, {}).get(tool.method_name or "")
    if schema is None:
        return {}
    existing = tool.metadata.extra if tool.metadata else {}
    return {"extra": {**(existing or {}), "output_schema": schema}}


def _apply_output_schemas(
    registry: ToolRegistry, names: Set[str] | None = None
) -> None:
    """Publish the declared result schemas of the registered tools.

    A declared schema lives in ``ToolMetadata.extra["output_schema"]``
    because that is where ``toolregistry-server`` reads it.  Metadata
    declarations themselves are applied at definition time; this pass only
    attaches the schemas keyed by namespace and method in
    ``OUTPUT_SCHEMAS``.

    Args:
        registry: The registry whose tools should be annotated.
        names: When given, annotate only these tools.  A hot reload passes
            the names it registered.
    """
    updates: list[tuple[str, dict]] = []
    for tool in registry._tools.values():
        if names is not None and tool.name not in names:
            continue
        update = _output_schema_update(tool.namespace, tool)
        if update:
            updates.append((tool.name, update))
    for name, update in updates:
        registry._replace_tool_metadata(name, **update)


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
    reload_state: ReloadState | None = None,
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
        reload_state: When given, registration is tracked source by source
            and the state is filled in so a :class:`ConfigWatcher` can diff a
            later version of the file (#144).

    Returns:
        A fully configured ``ToolRegistry`` instance.
    """
    from toolregistry_server import apply_config

    config = _resolve_config(tools_config_path)

    registry = ToolRegistry(name="hub", think_augment=enable_think)
    if not enable_discovery:
        # Core 0.20 runs discovery in "auto" mode by default: the first
        # deferred tool registered later (for example by a config reload)
        # starts discovery and adds ``discover_tools`` / ``call_deferred``.
        # That contradicts this flag, and the registration happens inside a
        # change callback, which can mutate ``_tools`` while a reload is
        # iterating it.  Pin the mode off when discovery was not requested.
        set_discovery_mode = getattr(registry, "set_tool_discovery_mode", None)
        if callable(set_discovery_mode):
            set_discovery_mode("off")
    registry.add_post_register_hook(configurable_hook)

    if reload_state is None:
        # Register tools from config (built-in defaults or user override)
        apply_config(registry, config)
    else:
        # Same registration, but record the names each source produced so a
        # reload can compare sources instead of rebuilding the registry.
        reload_state.config_path = config.source or None
        reload_state.config = config
        reload_state.source_tools = apply_config_tracked(
            registry, config, statuses=reload_state.source_status
        )
        reload_state.applied_sources = index_sources(config.tools)

    _apply_hub_overrides(registry, config)

    if enable_discovery:
        registry.enable_tool_discovery()

    return registry


def _apply_hub_overrides(registry: ToolRegistry, config: ToolConfig) -> None:
    """Apply Hub output schemas and declarations, then the user's overrides.

    ``@tool_metadata`` declarations are applied by ``Tool.from_function`` on
    a core that provides the decorator; ``apply_declared_metadata`` is the
    released-floor fallback and is a no-op elsewhere.
    """
    _apply_output_schemas(registry)
    apply_declared_metadata(registry)

    # Re-apply user config overrides so they take precedence over hub defaults
    if config.tool_metadata:
        registry.apply_metadata_config(config.tool_metadata)


def apply_hub_overrides(registry: ToolRegistry, names: Set[str]) -> None:
    """Apply Hub defaults to the tools registered by a reload.

    ``reload_registry`` calls this before it applies the file's
    ``tool_metadata``, so the order is the same as :func:`build_registry`:
    Hub defaults first, the user's file overrides last.

    Only *names* are annotated.  Tools that already existed are skipped, so
    a value changed from the admin panel survives an unrelated config
    reload.  On a core that applies declarations itself, only the output
    schemas need this pass.

    Args:
        registry: Live registry, already updated by the reload.
        names: Tools registered by the reload that triggered this callback.
    """
    _apply_output_schemas(registry, names)
    apply_declared_metadata(registry, names)


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
