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

from __future__ import annotations

from dataclasses import fields as dataclass_fields
from typing import Any

from toolregistry import ToolRegistry
from toolregistry.config import PythonSource, ToolConfig
from toolregistry.tool import ToolMetadata, ToolTag

from .._vendor.structlog import get_logger
from ..utils.configurable import Configurable

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
    PythonSource(
        class_path="toolregistry_hub.academics.academic_search.AcademicSearch",
        namespace="academics",
    ),
]

# Metadata overrides for registered tools, keyed by namespace.
#
# Execution hints are what MCP hosts use to decide whether a call needs
# human approval (MCP 2025-06-18 annotations).  They are set explicitly
# here rather than left to the tag-derived defaults so that every tool in
# the hub makes a claim: a host that treats a missing ``readOnlyHint`` as
# write-capable would otherwise prompt for ``datetime-now``.
# ``idempotent_hint`` / ``open_world_hint`` are never derived from tags,
# so they are declared alongside.  See #280.
_TOOL_METADATA: dict[str, dict] = {
    "calculator": {
        "defer": True,
        "tags": {ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
    },
    "datetime": {
        "tags": {ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
        "methods": {
            "convert_timezone": {"defer": True, "title": "Convert Timezone"},
            "now": {"title": "Current Date and Time"},
        },
    },
    "think": {
        "tags": {ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
        "methods": {"think": {"title": "Think"}},
    },
    "file_ops": {
        "tags": {ToolTag.FILE_SYSTEM, ToolTag.DESTRUCTIVE},
        "read_only_hint": False,
        "destructive_hint": True,
        "open_world_hint": False,
        "methods": {
            "read": {
                "read_only_hint": True,
                "destructive_hint": False,
                "idempotent_hint": True,
                "title": "Read File",
            },
            "edit": {"idempotent_hint": False, "title": "Edit File"},
            "write": {"idempotent_hint": True, "title": "Write File"},
        },
    },
    "web/fetch": {
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": True,
        "methods": {"fetch_content": {"title": "Fetch URL Content"}},
    },
    "web/websearch": {
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": False,
        "open_world_hint": True,
        "methods": {
            "list_engines": {"defer": True, "idempotent_hint": True},
            "search": {"title": "Web Search"},
        },
    },
    "reader": {
        "defer": True,
        "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
    },
    "fs/file_search": {
        "defer": True,
        "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
    },
    "fs/path_info": {
        "defer": True,
        "tags": {ToolTag.FILE_SYSTEM, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
        "methods": {"info": {"title": "Path Info"}},
    },
    "bash": {
        "defer": True,
        "tags": {ToolTag.DESTRUCTIVE, ToolTag.PRIVILEGED},
        "read_only_hint": False,
        "destructive_hint": True,
        "idempotent_hint": False,
        "open_world_hint": True,
        "methods": {"execute": {"title": "Execute Shell Command"}},
    },
    "cron": {
        "defer": True,
        "tags": {ToolTag.PRIVILEGED},
        "read_only_hint": False,
        "destructive_hint": True,
        "open_world_hint": False,
        "methods": {
            "create": {
                "destructive_hint": False,
                "idempotent_hint": False,
                "title": "Schedule Job",
            },
            "delete": {"idempotent_hint": True, "title": "Delete Scheduled Job"},
            "list": {
                "read_only_hint": True,
                "destructive_hint": False,
                "idempotent_hint": True,
                "title": "List Scheduled Jobs",
            },
            "shutdown": {"idempotent_hint": True, "title": "Stop Scheduler"},
        },
    },
    "todolist": {
        "defer": True,
        # ``update`` renders the list the caller passes and stores nothing;
        # the host keeps the state. Read-only, matching the existing tag, so
        # permission behaviour does not change.
        "tags": {ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
        "methods": {"update": {"title": "Update Todo List"}},
    },
    "unit_converter": {
        "defer": True,
        "tags": {ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": True,
        "open_world_hint": False,
    },
    "weather": {
        "defer": True,
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": False,
        "open_world_hint": True,
        "methods": {
            "get_current": {"title": "Current Weather"},
            "get_forecast": {"title": "Weather Forecast"},
            "get_astronomy": {"title": "Astronomy"},
        },
    },
    "academics": {
        "tags": {ToolTag.NETWORK, ToolTag.READ_ONLY},
        "read_only_hint": True,
        "idempotent_hint": False,
        "open_world_hint": True,
        "methods": {
            "list_engines": {"defer": True, "idempotent_hint": True},
            "search": {"title": "Academic Search"},
        },
    },
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


def _collect_overrides(overrides: dict) -> dict[str, Any]:
    """Extract metadata update fields from an overrides dict.

    Returns a dict suitable for passing as kwargs to
    ``registry._replace_tool_metadata()``.

    Args:
        overrides: Dict with optional ``defer``, ``tags``, ``search_hint``,
            ``title`` and execution-hint keys (``read_only_hint``,
            ``destructive_hint``, ``idempotent_hint``, ``open_world_hint``).

    Returns:
        A dict of metadata field updates (may be empty).  Keys the installed
        :class:`ToolMetadata` does not define are dropped.
    """
    updates: dict = {}
    for key in (
        "defer",
        "tags",
        "search_hint",
        "title",
        "read_only_hint",
        "destructive_hint",
        "idempotent_hint",
        "open_world_hint",
    ):
        if key in overrides and key in _METADATA_FIELDS:
            updates[key] = overrides[key]
    return updates


def _apply_tool_metadata(registry: ToolRegistry) -> None:
    """Apply tag and defer overrides from ``_TOOL_METADATA`` to all tools.

    Namespace-level overrides are applied first; method-level overrides
    (nested under the ``methods`` key) are merged on top.  Uses
    ``_replace_tool_metadata()`` since Tool and ToolMetadata are frozen.

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
    # Collect all updates first — _replace_tool_metadata mutates the
    # _tools dict, so we cannot modify it while iterating.
    updates: list[tuple[str, dict]] = []
    for tool in registry._tools.values():
        ns = tool.namespace
        if not ns or ns not in _TOOL_METADATA:
            continue
        ns_meta = _TOOL_METADATA[ns]
        merged = _collect_overrides(ns_meta)
        method_overrides: dict[str, dict] = ns_meta.get("methods", {})
        if (
            method_overrides
            and tool.method_name
            and tool.method_name in method_overrides
        ):
            merged.update(_collect_overrides(method_overrides[tool.method_name]))
        if merged:
            updates.append((tool.name, merged))

    for name, meta_updates in updates:
        registry._replace_tool_metadata(name, **meta_updates)


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
