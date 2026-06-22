"""Command-line interface for ToolRegistry Hub Server.

Reuses toolregistry-server's CLI infrastructure via ``run_cli``,
providing Hub-specific banner, version check, and dispatch.

Usage:
    toolregistry-hub openapi [OPTIONS]
    toolregistry-hub mcp [OPTIONS]
"""

import argparse
from typing import NoReturn

from .. import __version__
from .._vendor.structlog import get_logger
from .banner import BANNER_ART

logger = get_logger()


# ---------------------------------------------------------------------------
# Hub-specific version / banner
# ---------------------------------------------------------------------------


def _get_version_string() -> str:
    """Build Hub version string with update check."""
    import asyncio

    from ..version_check import check_for_updates

    try:
        try:
            asyncio.get_running_loop()
            return f"toolregistry-hub {__version__}"
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                info = loop.run_until_complete(check_for_updates())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        if info["update_available"]:
            return (
                f"toolregistry-hub {info['current_version']}\n"
                f"Update available: v{info['latest_version']}\n"
                "Run: pip install --upgrade toolregistry-hub"
            )
        return f"toolregistry-hub {info['current_version']} (Latest)"
    except Exception:
        return f"toolregistry-hub {__version__}"


def _print_hub_banner() -> None:
    """Print Hub banner with version check."""
    import asyncio

    from toolregistry_server.cli import print_banner

    from ..version_check import check_for_updates

    try:
        try:
            asyncio.get_running_loop()
            version = __version__
            extra_lines = None
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                info = loop.run_until_complete(check_for_updates())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

            if info["update_available"]:
                version = info["current_version"]
                extra_lines = [
                    f"UPDATE AVAILABLE: v{info['latest_version']}",
                    "Run: pip install --upgrade toolregistry-hub",
                ]
            else:
                version = f"{info['current_version']} (Latest)"
                extra_lines = None
    except Exception:
        version = __version__
        extra_lines = None

    print_banner(version=version, banner_art=BANNER_ART, extra_lines=extra_lines)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _add_hub_arguments(parser: argparse.ArgumentParser) -> None:
    """Add Hub-specific arguments on top of server defaults."""
    parser.add_argument(
        "--admin-port",
        type=int,
        default=None,
        metavar="PORT",
        help="Enable the admin panel on the specified port (e.g. 8081)",
    )
    parser.add_argument(
        "--tool-discovery",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable tool discovery (default: enabled)",
    )
    parser.add_argument(
        "--think-augment",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable/disable think-augmented function calling (default: enabled)",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the Hub CLI argument parser."""
    from toolregistry_server.adapters.mcp import MCPAdapter
    from toolregistry_server.adapters.openapi import OpenAPIAdapter

    parser = argparse.ArgumentParser(
        prog="toolregistry-hub",
        description="ToolRegistry Hub - Pre-configured tool server",
    )
    parser.add_argument("--version", "-V", action="store_true", help="Show version")
    parser.add_argument("--no-banner", action="store_true", help="Disable banner")

    sub = parser.add_subparsers(dest="command", metavar="{openapi,mcp}")

    openapi = sub.add_parser("openapi", help="Start OpenAPI server")
    OpenAPIAdapter.add_cli_arguments(openapi)
    _add_hub_arguments(openapi)

    mcp = sub.add_parser("mcp", help="Start MCP server")
    MCPAdapter.add_cli_arguments(mcp)
    _add_hub_arguments(mcp)

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def _hub_dispatch(parsed: argparse.Namespace) -> None:
    """Dispatch parsed args to HubApp."""
    from .app import HubApp

    app = HubApp()
    common = {
        "tools_config_path": getattr(parsed, "config", None),
        "enable_discovery": getattr(parsed, "tool_discovery", True),
        "enable_think": getattr(parsed, "think_augment", True),
        "profile": getattr(parsed, "profile", None),
        "admin_port": getattr(parsed, "admin_port", None),
    }

    if parsed.command == "openapi":
        app.serve_openapi(
            host=parsed.host,
            port=parsed.port,
            tokens_path=getattr(parsed, "tokens", None),
            reload=getattr(parsed, "reload", False),
            **common,
        )
    elif parsed.command == "mcp":
        app.serve_mcp(
            transport=parsed.transport,
            host=parsed.host,
            port=parsed.port,
            **common,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(args: list[str] | None = None) -> NoReturn | None:
    """Main entry point for the Hub CLI."""
    from toolregistry_server.cli import run_cli

    parsed = create_parser().parse_args(args)
    return run_cli(
        parsed,
        version_string=_get_version_string(),
        banner_fn=_print_hub_banner,
        dispatch_fn=_hub_dispatch,
    )


if __name__ == "__main__":
    main()
