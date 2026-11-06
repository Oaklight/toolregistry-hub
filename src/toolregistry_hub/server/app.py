"""Hub server application — subclass of toolregistry_server.App.

Overrides :meth:`prepare_registry` to build the Hub registry with
built-in tools, configurable hook, and metadata overrides.

Example::

    from toolregistry_hub.server.app import HubApp
    app = HubApp()
    app.serve_openapi(host="0.0.0.0", port=8000)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from toolregistry_server import ServerIdentity
from toolregistry_server.app import App

from .. import __version__
from .._vendor.structlog import get_logger
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


class HubApp(App):
    """Hub-specific server application."""

    def __init__(self, identity: ServerIdentity | None = None) -> None:
        super().__init__(identity=identity or HUB_IDENTITY)
        self.config_watcher: ConfigWatcher | None = None

    def prepare_registry(self, **kwargs) -> ToolRegistry:
        """Build the Hub registry.

        Keyword Args:
            tools_config_path: Path to a JSONC/YAML config file override.
            enable_discovery: Enable BM25 tool discovery.
            enable_think: Enable think-augmented function calling.
            profile: Deployment profile for tag-based filtering.
            admin_port: Port for the admin panel, or None to disable.
            config_reload: Watch the config file and apply edits to the live
                registry (#144).
        """
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

        admin_port = kwargs.get("admin_port")
        if admin_port is not None:
            registry.enable_logging()
            admin_host = kwargs.get("host", "127.0.0.1")
            info = registry.enable_admin(host=admin_host, port=admin_port)
            logger.info(f"Admin panel enabled at {info.url}")

        if reload_state is not None:
            self._start_config_watcher(registry, reload_state)

        return registry

    def _start_config_watcher(self, registry: ToolRegistry, state: ReloadState) -> None:
        """Start the tools.jsonc watcher, or explain why it cannot run."""
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
        logger.info(f"Config hot reload watching {state.config_path}")


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
