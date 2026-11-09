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
from ._compat import SERVER_HAS_GATEWAY, SERVER_HAS_SOURCE_MANAGER
from .app import HubApp

logger = get_logger()


class HubCLI(CLI):
    """Hub CLI — extends server CLI with Hub-specific features."""

    def __init__(self) -> None:
        super().__init__(app=HubApp())

    def configure_subparsers(
        self, subparsers: dict[str, argparse.ArgumentParser]
    ) -> None:
        """Add Hub-specific arguments to each subparser."""
        for sub_parser in subparsers.values():
            _add_hub_arguments(sub_parser)
        if SERVER_HAS_GATEWAY:
            # Say which serving path each command takes: on a server with the
            # gateway, the openapi command and the HTTP MCP transports are
            # served through it, while stdio stays a direct MCP server.
            subparsers[
                "openapi"
            ].description = "Start the OpenAPI frontend through the server gateway."
            subparsers["mcp"].description = (
                "Start the MCP server. stdio is served directly; "
                "streamable-http and sse use the server gateway."
            )

    def get_version_string(self) -> str:
        """Hub version with update check."""
        return _get_version_string()

    def print_banner(self) -> None:
        """Print Hub banner with PyPI update check.

        Overrides the base implementation because Hub needs to
        check for updates and display extra lines — logic that
        the base ``ServerIdentity``-driven banner doesn't support.
        """
        _print_hub_banner()

    def dispatch(self, parsed: argparse.Namespace) -> None:
        """Route to HubApp with Hub-specific kwargs.

        On a server that provides the gateway, ``openapi`` and the HTTP MCP
        transports are served through it so both frontends share one code
        path.  ``mcp --transport stdio`` stays on the direct MCP server: the
        gateway has no stdio frontend.
        """
        common = {
            "tools_config_path": getattr(parsed, "config", None),
            "enable_discovery": getattr(parsed, "tool_discovery", True),
            "enable_think": getattr(parsed, "think_augment", True),
            "profile": getattr(parsed, "profile", None),
            "admin_port": getattr(parsed, "admin_port", None),
            # tools.jsonc hot reload (#144); off unless --config-reload is given.
            "config_reload": getattr(parsed, "config_reload", False),
            # The server adds --no-config-write next to --config-reload on a
            # server that has the source manager; the released floor has
            # neither flag and always keeps changes in memory.
            "write_config": getattr(parsed, "config_write", True),
        }
        transport = getattr(parsed, "transport", None)
        # The gateway takes the union of the frontend options: host/port,
        # credentials, backend, the OAuth origin and the tools/list cache
        # hints.  The released-floor calls below keep their original, narrower
        # kwarg sets.
        gateway_options = {
            "host": parsed.host,
            "port": parsed.port,
            "tokens_path": getattr(parsed, "tokens", None),
            "reload": getattr(parsed, "reload", False),
            "backend": getattr(parsed, "backend", "fastapi"),
            "server_url": getattr(parsed, "server_url", None),
            "tools_list_ttl_ms": getattr(parsed, "tools_list_ttl_ms", None),
            "tools_list_cache_scope": getattr(parsed, "tools_list_cache_scope", None),
            "strict_spec_regex": getattr(parsed, "strict_spec_regex", False),
        }

        if parsed.command == "openapi":
            if SERVER_HAS_GATEWAY:
                self.app.serve_gateway(
                    openapi_enabled=True,
                    mcp_enabled=False,
                    sse_enabled=False,
                    **gateway_options,
                    **common,
                )
            else:
                self.app.serve_openapi(
                    host=parsed.host,
                    port=parsed.port,
                    tokens_path=getattr(parsed, "tokens", None),
                    reload=getattr(parsed, "reload", False),
                    # The Hub builds these kwargs explicitly, so a flag added
                    # to the server subparser is dropped unless forwarded
                    # (#78, #83).  ``backend`` selects fastapi or httpserver;
                    # the default matches the server's own default.
                    backend=getattr(parsed, "backend", "fastapi"),
                    **common,
                )
        elif parsed.command == "mcp":
            if SERVER_HAS_GATEWAY and transport != "stdio":
                self.app.serve_gateway(
                    openapi_enabled=False,
                    mcp_enabled=transport in ("streamable-http", "http"),
                    sse_enabled=transport == "sse",
                    **gateway_options,
                    **common,
                )
            else:
                self.app.serve_mcp(
                    transport=transport,
                    host=parsed.host,
                    port=parsed.port,
                    # Public origin for OAuth protected-resource metadata.  The
                    # Hub builds serve_mcp kwargs explicitly, so the flag the
                    # server subparser adds has to be forwarded here or it is
                    # silently dropped (#78).
                    server_url=getattr(parsed, "server_url", None),
                    # tools/list cache hints, same reasoning: built explicitly
                    # here, so an added server flag is dropped unless
                    # forwarded (#83).
                    tools_list_ttl_ms=getattr(parsed, "tools_list_ttl_ms", None),
                    tools_list_cache_scope=getattr(
                        parsed, "tools_list_cache_scope", None
                    ),
                    **common,
                )
        elif parsed.command == "gateway":
            # The server adds this subcommand on a build with the gateway; it
            # is not present on the released floor, so this branch cannot run
            # there.
            extras = {
                key: value
                for key in (
                    "openapi_path",
                    "mcp_path",
                    "sse_path",
                    "max_body_size",
                    "regex_timeout",
                    "regex_budget",
                )
                if (value := getattr(parsed, key, None)) is not None
            }
            self.app.serve_gateway(
                openapi_enabled=getattr(parsed, "openapi", None),
                mcp_enabled=getattr(parsed, "mcp", None),
                sse_enabled=getattr(parsed, "sse", None),
                **extras,
                **gateway_options,
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
    # A server with the runtime source manager adds --config-reload (and
    # --no-config-write) to these subparsers itself, so defining it again
    # would make argparse reject the duplicate option.
    if not SERVER_HAS_SOURCE_MANAGER:
        parser.add_argument(
            "--config-reload",
            action=argparse.BooleanOptionalAction,
            default=False,
            help=(
                "Reload tools.jsonc when the file changes (default: disabled). "
                "Requires a config file; the built-in default list has nothing "
                "to watch."
            ),
        )


def _run_update_check() -> dict | None:
    """Run the async update check synchronously.

    Returns the update info dict, or ``None`` if a running event
    loop is detected or the check fails.
    """
    import asyncio

    from ..version_check import check_for_updates

    try:
        asyncio.get_running_loop()
        return None  # can't block inside an existing loop
    except RuntimeError:
        pass

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(check_for_updates())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    except Exception:
        return None


def _get_version_string() -> str:
    """Build Hub version string with update check."""
    info = _run_update_check()
    if info is None:
        return f"toolregistry-hub {__version__}"
    if info["update_available"]:
        return (
            f"toolregistry-hub {info['current_version']}\n"
            f"Update available: v{info['latest_version']}\n"
            "Run: pip install --upgrade toolregistry-hub"
        )
    return f"toolregistry-hub {info['current_version']} (Latest)"


def _print_hub_banner() -> None:
    """Print Hub banner with version check."""
    from toolregistry_server.cli import print_banner

    from .banner import BANNER_ART

    info = _run_update_check()
    if info is None:
        version = __version__
        extra_lines = None
    elif info["update_available"]:
        version = info["current_version"]
        extra_lines = [
            f"UPDATE AVAILABLE: v{info['latest_version']}",
            "Run: pip install --upgrade toolregistry-hub",
        ]
    else:
        version = f"{info['current_version']} (Latest)"
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
