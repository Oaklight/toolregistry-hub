"""Hub server application — subclass of toolregistry_server.App.

Overrides :meth:`prepare_registry` to build the Hub registry with
built-in tools, configurable hook, and metadata overrides.

Example::

    from toolregistry_hub.server.app import HubApp
    app = HubApp()
    app.serve_openapi(host="0.0.0.0", port=8000)
"""

from __future__ import annotations

import atexit
from typing import TYPE_CHECKING

from toolregistry_server import ServerIdentity
from toolregistry_server.app import App

from .. import __version__
from .._vendor.structlog import get_logger
from ._compat import SERVER_HAS_SOURCE_MANAGER
from .banner import BANNER_ART

logger = get_logger()

if TYPE_CHECKING:
    from toolregistry import ToolRegistry

    from .hot_reload import ConfigWatcher, ReloadState

HUB_IDENTITY = ServerIdentity(
    name="ToolRegistry Hub",
    version=__version__,
    description="Pre-configured tool server with various utilities",
    banner_art=BANNER_ART,
)


def _pin_discovery(registry: ToolRegistry, enabled: bool) -> None:
    """Keep discovery off when it was not requested.

    Core 0.20 runs discovery in "auto" mode by default: the first deferred
    tool registered later (for example by a config reload) starts discovery
    and adds ``discover_tools`` / ``call_deferred``.  That contradicts the
    flag, and the registration happens inside a change callback, which can
    mutate ``_tools`` while a reload is iterating it.
    """
    if enabled:
        return
    set_discovery_mode = getattr(registry, "set_tool_discovery_mode", None)
    if callable(set_discovery_mode):
        set_discovery_mode("off")


def _enable_admin(registry: ToolRegistry, **kwargs) -> None:
    """Enable the admin panel when a port was requested."""
    admin_port = kwargs.get("admin_port")
    if admin_port is None:
        return
    registry.enable_logging()
    admin_host = kwargs.get("host", "127.0.0.1")
    info = registry.enable_admin(host=admin_host, port=admin_port)
    logger.info(f"Admin panel enabled at {info.url}")


class HubApp(App):
    """Hub-specific server application."""

    def __init__(self, identity: ServerIdentity | None = None) -> None:
        super().__init__(identity=identity or HUB_IDENTITY)
        self.config_watcher: ConfigWatcher | None = None

    def prepare_registry(self, **kwargs) -> ToolRegistry:
        """Build the Hub registry.

        On a server that provides the runtime source manager, the manager
        owns registration: it applies the preset (or the config file),
        records each source's tools, and hands them to the Hub's metadata and
        output-schema pass.  On the released floor the previous
        ``build_registry`` path runs instead.

        Keyword Args:
            tools_config_path: Path to a JSONC/YAML config file override.
            enable_discovery: Enable BM25 tool discovery.
            enable_think: Enable think-augmented function calling.
            profile: Deployment profile for tag-based filtering.
            admin_port: Port for the admin panel, or None to disable.
            config_reload: Watch the config file and apply edits to the live
                registry (#144).
            write_config: Persist runtime source changes back to the config
                file.  Only read on a server that has the source manager.
        """
        if SERVER_HAS_SOURCE_MANAGER:
            return self._prepare_registry_with_manager(**kwargs)
        return self._prepare_registry_on_released_server(**kwargs)

    def _prepare_registry_with_manager(self, **kwargs) -> ToolRegistry:
        """Build the registry through the server's runtime source manager."""
        from toolregistry import ToolRegistry
        from toolregistry_server.source_manager import SourceManager

        from .registry import _resolve_config, apply_hub_overrides, configurable_hook

        config = _resolve_config(kwargs.get("tools_config_path"))
        registry = ToolRegistry(
            name="hub", think_augment=kwargs.get("enable_think", True)
        )
        _pin_discovery(registry, kwargs.get("enable_discovery", True))
        registry.add_post_register_hook(configurable_hook)
        manager = SourceManager(
            registry,
            config,
            config_path=config.source or None,
            profile=kwargs.get("profile"),
            write_config=kwargs.get("write_config", True),
            on_registered=apply_hub_overrides,
        )
        manager.apply_initial()
        self.source_manager = manager
        if kwargs.get("enable_discovery", True):
            registry.enable_tool_discovery()
        _enable_admin(registry, **kwargs)
        return registry

    def _prepare_registry_on_released_server(self, **kwargs) -> ToolRegistry:
        """Build the registry with the released-floor registration path."""
        from toolregistry_server import apply_profile

        from .hot_reload import ReloadState
        from .registry import build_registry

        reload_state = ReloadState() if kwargs.get("config_reload") else None
        registry = build_registry(
            tools_config_path=kwargs.get("tools_config_path"),
            enable_discovery=kwargs.get("enable_discovery", True),
            enable_think=kwargs.get("enable_think", True),
            reload_state=reload_state,
        )

        profile = kwargs.get("profile")
        if profile is not None:
            apply_profile(registry, profile)
            if reload_state is not None:
                # New tools registered by a reload must obey the same
                # profile filter as the startup registry.
                reload_state.profile = profile

        _enable_admin(registry, **kwargs)

        if reload_state is not None:
            self._start_hub_config_watcher(registry, reload_state)

        return registry

    def _start_hub_config_watcher(
        self, registry: ToolRegistry, state: ReloadState
    ) -> None:
        """Start the Hub's tools.jsonc watcher (released-floor fallback).

        A server with the runtime source manager starts its own watcher from
        :meth:`toolregistry_server.app.App._attach_source_manager`; this
        method is only used when that manager is absent.
        """
        from .hot_reload import ConfigWatcher
        from .registry import apply_hub_overrides

        if not state.config_path:
            logger.warning(
                "--config-reload was requested, but no config file was found "
                "(TOOLS_CONFIG / tools.jsonc); the built-in defaults have "
                "nothing to watch."
            )
            return

        self.config_watcher = ConfigWatcher(
            registry,
            state,
            on_reload=apply_hub_overrides,
        )
        self.config_watcher.start()
        # Stop the thread cleanly on interpreter exit.  It is a daemon, but
        # asking it to stop avoids a reload mutating the registry while the
        # process is tearing down.
        atexit.register(self.stop_config_watcher)
        logger.info(f"Config hot reload watching {state.config_path}")

    def stop_config_watcher(self, timeout: float | None = 2.0) -> None:
        """Stop the config watcher, if one is running.

        Args:
            timeout: Seconds to wait for the thread to finish.  ``None``
                returns immediately.
        """
        if SERVER_HAS_SOURCE_MANAGER:
            # The watcher belongs to the server and is stopped by its own
            # implementation; this override exists for the released floor.
            stop = getattr(super(), "stop_config_watcher", None)
            if stop is not None:
                stop(timeout=timeout)
            return
        watcher = self.config_watcher
        if watcher is None:
            return
        watcher.stop(timeout)
        self.config_watcher = None


# Module-level convenience (lazy-init default HubApp)

_app: HubApp | None = None


def _get_default_app() -> HubApp:
    """Return the shared default HubApp, creating it on first use."""
    global _app
    if _app is None:
        _app = HubApp()
    return _app


def serve_openapi(**kwargs) -> None:
    """Build registry and start an OpenAPI server."""
    _get_default_app().serve_openapi(**kwargs)


def serve_mcp(**kwargs) -> None:
    """Build registry and start an MCP server."""
    _get_default_app().serve_mcp(**kwargs)
