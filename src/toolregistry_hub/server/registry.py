"""Central tool registry for ToolRegistry Hub.

This module holds the Hub preset and the single registration path:

- ``data/tools.yaml``: the default tool list, shipped inside the package
  and loaded unless an explicit or discovered config file replaces it
- ``@tool_metadata`` (core): tags, ``defer``, hints and output schemas
  declared on the tool methods themselves
- ``configurable_hook``: post-register hook that auto-disables unconfigured
  tools

Registration is owned by the server's runtime source manager, the same path
``toolregistry-server`` uses: it applies the preset (or the config file) and
records each source's tools.  The Hub keeps no watcher and no source diff of
its own, and no override pass: the core applies each method's declaration
when it builds the tool.

Deployment-context filtering (``--profile``) is handled by
``toolregistry-server`` and is not reimplemented here.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from toolregistry import ToolRegistry
from toolregistry.config import ToolConfig

from .._vendor.structlog import get_logger
from ..utils.configurable import Configurable

logger = get_logger()


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


def _discover_config_path() -> str | None:
    """Auto-discover a tool config file path.

    Checks ``TOOLS_CONFIG`` env var, then ``tools.jsonc``, ``tools.yaml``,
    and ``tools.yml`` in the current directory.

    Returns:
        A file path string if a config file is found, else ``None``.
    """
    import os

    env_path = os.environ.get("TOOLS_CONFIG")
    if env_path and Path(env_path).is_file():
        return env_path
    for candidate in ("tools.jsonc", "tools.yaml", "tools.yml"):
        if Path(candidate).is_file():
            return candidate
    return None


def default_preset_path() -> Path:
    """Return the path of the packaged default tool preset.

    Returns:
        ``toolregistry_hub/data/tools.yaml`` inside the installed package.
    """
    return Path(__file__).resolve().parent.parent / "data" / "tools.yaml"


def load_default_preset() -> ToolConfig:
    """Load the packaged preset as the default tool list.

    ``source`` is cleared before returning: the runtime write-back path keys
    off it, and a runtime source change must stay in memory rather than
    rewrite a file inside the installed package.

    Returns:
        The packaged ``ToolConfig``.
    """
    from toolregistry_server import load_config

    config = load_config(str(default_preset_path()))
    # ``ToolConfig`` is frozen; the replacement keeps every parsed field and
    # clears only the diagnostic source path.
    return dataclasses.replace(config, source="")


def _resolve_config(
    tools_config_path: str | None = None,
) -> ToolConfig:
    """Load or build the tool config to register from.

    Priority: explicit path > auto-discovery
    (``TOOLS_CONFIG`` env var / ``tools.jsonc`` / ``tools.yaml``) > the
    packaged ``data/tools.yaml`` preset.

    A path that names the packaged preset is treated as the built-in default:
    the launcher injects it as ``--config`` so the server dispatch always has
    one, and a runtime source change must stay in memory rather than rewrite
    a file inside the installed package.

    Args:
        tools_config_path: Explicit config file path, or ``None``.

    Returns:
        A ``ToolConfig`` ready for registration.
    """
    from toolregistry_server import load_config

    path = tools_config_path or _discover_config_path()
    if path is not None:
        if Path(path).resolve() == default_preset_path().resolve():
            return load_default_preset()
        config = load_config(path)
        if config.tools:
            return config

    return load_default_preset()


def _pin_discovery(registry: ToolRegistry, enabled: bool) -> None:
    """Keep discovery off when it was not requested.

    Core 0.20 runs discovery in "auto" mode by default: the first deferred
    tool registered later (for example by a source-manager diff) starts
    discovery and adds ``discover_tools`` / ``call_deferred``.  That
    contradicts the flag, and the registration happens inside a change
    callback, which can mutate ``_tools`` while a mutation is iterating it.
    """
    if enabled:
        return
    set_discovery_mode = getattr(registry, "set_tool_discovery_mode", None)
    if callable(set_discovery_mode):
        set_discovery_mode("off")


def build_hub_registry(
    tools_config_path: str | None = None,
    enable_discovery: bool = True,
    enable_think: bool = True,
    profile: str | None = None,
    write_config: bool = True,
) -> tuple[ToolRegistry, Any]:
    """Build the Hub registry and its runtime source manager.

    The server's :class:`SourceManager` owns registration: it applies the
    preset (or the config file) and records each source's tools.  Method
    declarations reach the tools through the core decorator, so no Hub
    callback is needed.

    Args:
        tools_config_path: Path to a JSONC/YAML config file, or ``None`` for
            auto-discovery (``TOOLS_CONFIG`` env var / ``tools.jsonc``).
        enable_discovery: Register ``discover_tools`` and mark deferred tools.
        enable_think: Inject ``toolcall_reason`` into tool schemas.
        profile: Deployment profile for tag-based filtering.
        write_config: Persist runtime source changes back to the config file.

    Returns:
        ``(registry, manager)``.  The launcher stores the manager on the app
        so runtime source changes and the config watcher reach the live
        registry; callers that only need the tools ignore it.
    """
    from toolregistry_server import apply_profile
    from toolregistry_server.source_manager import SourceManager

    config = _resolve_config(tools_config_path)

    registry = ToolRegistry(name="hub", think_augment=enable_think)
    _pin_discovery(registry, enable_discovery)
    registry.add_post_register_hook(configurable_hook)

    manager = SourceManager(
        registry,
        config,
        config_path=config.source or None,
        profile=profile,
        write_config=write_config,
    )
    manager.apply_initial()

    if profile is not None:
        # ``apply_initial`` registers startup sources without the profile
        # filter; later diffs are filtered by the manager itself.
        apply_profile(registry, profile)

    if enable_discovery:
        registry.enable_tool_discovery()

    return registry, manager


def build_registry(
    tools_config_path: str | None = None,
    enable_discovery: bool = True,
    enable_think: bool = True,
    profile: str | None = None,
    write_config: bool = True,
) -> ToolRegistry:
    """Build the Hub registry through the launcher's registration path.

    Convenience wrapper over :func:`build_hub_registry` for callers that only
    need the registry.

    Args:
        tools_config_path: Path to a JSONC/YAML config file, or ``None``.
        enable_discovery: Register ``discover_tools`` and mark deferred tools.
        enable_think: Inject ``toolcall_reason`` into tool schemas.
        profile: Deployment profile for tag-based filtering.
        write_config: Persist runtime source changes back to the config file.

    Returns:
        A fully configured ``ToolRegistry`` instance.
    """
    registry, _ = build_hub_registry(
        tools_config_path=tools_config_path,
        enable_discovery=enable_discovery,
        enable_think=enable_think,
        profile=profile,
        write_config=write_config,
    )
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
