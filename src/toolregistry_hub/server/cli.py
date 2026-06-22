"""Command-line interface for ToolRegistry Hub Server.

Subclasses :class:`toolregistry_server.cli.CLI` with Hub-specific
banner (version check), extra arguments, and dispatch.

Usage:
    toolregistry-hub openapi [OPTIONS]
    toolregistry-hub mcp [OPTIONS]
"""

from __future__ import annotations

import argparse
from typing import NoReturn

from toolregistry_server.cli import CLI

from .. import __version__
from .._vendor.structlog import get_logger
from .app import HubApp

logger = get_logger()


class HubCLI(CLI):
    """Hub CLI — extends server CLI with Hub-specific features."""

    def __init__(self) -> None:
        super().__init__(app=HubApp())

    def create_parser(self) -> argparse.ArgumentParser:
        """Add Hub-specific arguments to each subparser."""
        parser = super().create_parser()

        # Find subparsers and add hub args to each
        for action in parser._subparsers._actions:
            if isinstance(action, argparse._SubParsersAction):
                for sub_parser in action.choices.values():
                    _add_hub_arguments(sub_parser)

        return parser

    def get_version_string(self) -> str:
        """Hub version with update check."""
        return _get_version_string()

    def print_banner(self) -> None:
        """Hub banner with update check."""
        _print_hub_banner()

    def dispatch(self, parsed: argparse.Namespace) -> None:
        """Route to HubApp with Hub-specific kwargs."""
        common = {
            "tools_config_path": getattr(parsed, "config", None),
            "enable_discovery": getattr(parsed, "tool_discovery", True),
            "enable_think": getattr(parsed, "think_augment", True),
            "profile": getattr(parsed, "profile", None),
            "admin_port": getattr(parsed, "admin_port", None),
        }

        if parsed.command == "openapi":
            self.app.serve_openapi(
                host=parsed.host,
                port=parsed.port,
                tokens_path=getattr(parsed, "tokens", None),
                reload=getattr(parsed, "reload", False),
                **common,
            )
        elif parsed.command == "mcp":
            self.app.serve_mcp(
                transport=parsed.transport,
                host=parsed.host,
                port=parsed.port,
                **common,
            )


# ---------------------------------------------------------------------------
# Hub-specific helpers
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
    from .banner import BANNER_ART

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
# Entry point
# ---------------------------------------------------------------------------


def main(args: list[str] | None = None) -> NoReturn | None:
    """Main entry point for the Hub CLI."""
    return HubCLI().main(args)


if __name__ == "__main__":
    main()
