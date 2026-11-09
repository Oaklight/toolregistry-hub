"""Hub server application — subclass of toolregistry_server.App.

Overrides :meth:`prepare_registry` to build the Hub registry from the preset
through the server's runtime source manager.  Everything else — serving the
gateway, the config watcher, runtime source changes — is the server's.

Example::

    from toolregistry_hub.server.app import HubApp
    app = HubApp()
    app.serve_gateway(host="0.0.0.0", port=8000)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from toolregistry_server import ServerIdentity
from toolregistry_server.app import App

from .. import __version__
from .._vendor.structlog import get_logger
from .banner import BANNER_ART
from .registry import build_hub_registry

logger = get_logger()

if TYPE_CHECKING:
    from toolregistry import ToolRegistry

HUB_IDENTITY = ServerIdentity(
    name="ToolRegistry Hub",
    version=__version__,
    description="Pre-configured tool server with various utilities",
    banner_art=BANNER_ART,
)


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

    def prepare_registry(self, **kwargs) -> ToolRegistry:
        """Build the Hub registry through the server's source manager.

        ``--config-reload`` is not read here: :meth:`App.create_gateway`
        passes the same kwargs to :meth:`App._attach_source_manager`, which
        starts the server's ``ConfigWatcher`` on the manager returned below.
        Using ``App.serve``/``App.create_gateway`` therefore needs no Hub
        watcher or diff code.

        Keyword Args:
            tools_config_path: Path to a JSONC/YAML config file override.
            enable_discovery: Enable BM25 tool discovery.
            enable_think: Enable think-augmented function calling.
            profile: Deployment profile for tag-based filtering.
            admin_port: Port for the core admin panel, or None to disable.
            config_reload: Watch the config file and apply edits to the live
                registry.  Read by the server, not here.
            write_config: Persist runtime source changes back to the config
                file.
        """
        registry, manager = build_hub_registry(
            tools_config_path=kwargs.get("tools_config_path"),
            enable_discovery=kwargs.get("enable_discovery", True),
            enable_think=kwargs.get("enable_think", True),
            profile=kwargs.get("profile"),
            write_config=kwargs.get("write_config", True),
        )
        self.source_manager = manager
        _enable_admin(registry, **kwargs)
        return registry


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
