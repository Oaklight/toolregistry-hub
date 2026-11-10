"""Hub server application — subclass of toolregistry_server.App.

Overrides :meth:`prepare_registry` to build the Hub registry from the preset
through the server's runtime source manager.  Everything else — serving the
gateway, the config watcher, runtime source changes — is the server's.

The Hub-only policy flags (``--admin-port``, ``--tool-discovery`` and
``--think-augment``) are parsed by the launcher and carried on the app, so
the server command line never sees them.

Example::

    from toolregistry_hub.server.app import HubApp
    app = HubApp(admin_port=8081)
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
    """Hub-specific server application.

    Args:
        identity: Server identity to use instead of the Hub default.
        enable_discovery: Register the tool-discovery helpers.
        enable_think: Inject ``toolcall_reason`` into tool schemas.
        admin_port: Port for the core admin panel, or ``None`` to disable it.
    """

    def __init__(
        self,
        identity: ServerIdentity | None = None,
        *,
        enable_discovery: bool = True,
        enable_think: bool = True,
        admin_port: int | None = None,
    ) -> None:
        super().__init__(identity=identity or HUB_IDENTITY)
        self.enable_discovery = enable_discovery
        self.enable_think = enable_think
        self.admin_port = admin_port

    def prepare_registry(self, **kwargs) -> ToolRegistry:
        """Build the Hub registry through the server's source manager.

        The server dispatch passes ``config_path``; the Hub keeps accepting
        ``tools_config_path`` for callers that predate that name.  With
        neither, :func:`build_hub_registry` falls back to discovery and then
        to the packaged preset.

        ``--config-reload`` is not read here: :meth:`App.create_gateway`
        passes the same kwargs to :meth:`App._attach_source_manager`, which
        starts the server's ``ConfigWatcher`` on the manager returned below.
        Using ``App.serve``/``App.create_gateway`` therefore needs no Hub
        watcher or diff code.

        Keyword Args:
            config_path: Path to the tool config, as the server dispatch
                names it.
            tools_config_path: Alias for *config_path*.
            enable_discovery: Enable BM25 tool discovery.  Defaults to the
                app's constructor value.
            enable_think: Enable think-augmented function calling.  Defaults
                to the app's constructor value.
            profile: Deployment profile for tag-based filtering.
            admin_port: Port for the core admin panel, or ``None`` to
                disable.  Defaults to the app's constructor value.
            config_reload: Watch the config file and apply edits to the live
                registry.  Read by the server, not here.
            write_config: Persist runtime source changes back to the config
                file.
        """
        tools_config_path = kwargs.get("tools_config_path") or kwargs.get("config_path")
        registry, manager = build_hub_registry(
            tools_config_path=tools_config_path,
            enable_discovery=kwargs.get("enable_discovery", self.enable_discovery),
            enable_think=kwargs.get("enable_think", self.enable_think),
            profile=kwargs.get("profile"),
            write_config=kwargs.get("write_config", True),
        )
        self.source_manager = manager
        admin_kwargs = dict(kwargs)
        admin_kwargs.setdefault("admin_port", self.admin_port)
        _enable_admin(registry, **admin_kwargs)
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
