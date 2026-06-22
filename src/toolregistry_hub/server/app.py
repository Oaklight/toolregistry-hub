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

    def prepare_registry(self, **kwargs) -> ToolRegistry:
        """Build the Hub registry.

        Keyword Args:
            tools_config_path: Path to a JSONC/YAML config file override.
            enable_discovery: Enable BM25 tool discovery.
            enable_think: Enable think-augmented function calling.
            profile: Deployment profile for tag-based filtering.
            admin_port: Port for the admin panel, or None to disable.
        """
        from toolregistry_server import apply_profile

        from .registry import build_registry

        registry = build_registry(
            tools_config_path=kwargs.get("tools_config_path"),
            enable_discovery=kwargs.get("enable_discovery", True),
            enable_think=kwargs.get("enable_think", True),
        )

        profile = kwargs.get("profile")
        if profile is not None:
            apply_profile(registry, profile)

        admin_port = kwargs.get("admin_port")
        if admin_port is not None:
            registry.enable_logging()
            info = registry.enable_admin(port=admin_port)
            logger.info(f"Admin panel enabled at {info.url}")

        return registry


# Module-level convenience
_app = HubApp()

serve_openapi = _app.serve_openapi
serve_mcp = _app.serve_mcp
