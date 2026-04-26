"""Command-line interface for ToolRegistry Hub Server.

This module provides the CLI entry point for running ToolRegistry Hub servers
with support for both OpenAPI and MCP protocols.

The CLI reuses toolregistry-server's infrastructure but provides Hub-specific
banner, version information, and pre-configured tool registry.

Usage:
    toolregistry-hub openapi [OPTIONS]
    toolregistry-hub mcp [OPTIONS]
    toolregistry-hub --help

Example:
    # Start OpenAPI server on port 8000
    $ toolregistry-hub openapi --port 8000

    # Start MCP server with stdio transport
    $ toolregistry-hub mcp --transport stdio

    # Start MCP server with SSE transport
    $ toolregistry-hub mcp --transport sse --port 8000

    # With configuration file
    $ toolregistry-hub openapi --config tools.jsonc

    # With custom .env file
    $ toolregistry-hub openapi --env /path/to/.env

    # Skip loading .env file
    $ toolregistry-hub openapi --no-env
"""

import argparse
import sys
from typing import TYPE_CHECKING, NoReturn

from .. import __version__
from .._vendor.structlog import get_logger
from ..version_check import check_for_updates
from .banner import BANNER_ART

logger = get_logger()

if TYPE_CHECKING:
    from toolregistry import ToolRegistry


def _get_version_info() -> dict:
    """Get version information with update check.

    Returns:
        Dictionary with current_version, update_available, and latest_version.
    """
    import asyncio

    try:
        # Check if there's already a running event loop
        try:
            asyncio.get_running_loop()
            # If we're already in an event loop, skip async version check
            logger.debug(
                "Already in event loop, skipping async version check in banner"
            )
            return {
                "current_version": __version__,
                "update_available": False,
                "latest_version": None,
            }
        except RuntimeError:
            # No running loop, safe to create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(check_for_updates())
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    except Exception as e:
        logger.debug(f"Failed to check for updates in banner: {e}")
        return {
            "current_version": __version__,
            "update_available": False,
            "latest_version": None,
        }


def print_hub_banner() -> None:
    """Print the ToolRegistry Hub banner using toolregistry-server's print_banner.

    This function uses the shared print_banner from toolregistry-server,
    passing in the Hub-specific banner art and version information.
    """
    try:
        from toolregistry_server.cli import print_banner
    except ImportError:
        # Fallback if toolregistry-server is not installed
        logger.warning("toolregistry-server not installed, skipping banner")
        return

    # Get version info with update check
    version_info = _get_version_info()

    # Build extra lines for update notification
    extra_lines = None
    if version_info["update_available"]:
        extra_lines = [
            f"UPDATE AVAILABLE: v{version_info['latest_version']}",
            "Run: pip install --upgrade toolregistry-hub",
        ]

    # Build version string
    if version_info["update_available"]:
        version = version_info["current_version"]
    else:
        version = f"{version_info['current_version']} (Latest)"

    # Use toolregistry-server's print_banner with Hub customizations
    print_banner(
        version=version,
        banner_art=BANNER_ART,
        extra_lines=extra_lines,
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance with subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="toolregistry-hub",
        description="ToolRegistry Hub - Pre-configured tool server with various utilities",
    )

    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="Show version and exit",
    )

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Disable the startup banner",
    )

    # Create subparsers for openapi and mcp commands
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available server modes",
        metavar="{openapi,mcp}",
    )

    # OpenAPI subcommand
    openapi_parser = subparsers.add_parser(
        "openapi",
        help="Start OpenAPI (REST) server",
        description="Start an OpenAPI server exposing tools as REST endpoints",
    )
    _add_openapi_arguments(openapi_parser)

    # MCP subcommand
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Start MCP server",
        description="Start an MCP server for LLM tool integration",
    )
    _add_mcp_arguments(mcp_parser)

    return parser


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments shared by all subcommands.

    Args:
        parser: The ArgumentParser to add arguments to.
    """
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Path to .env file. Default: .env in current directory",
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help="Skip loading .env file",
    )
    parser.add_argument(
        "--admin-port",
        type=int,
        default=None,
        metavar="PORT",
        help="Enable the admin panel on the specified port (e.g. 8081)",
    )


def _add_openapi_arguments(parser: argparse.ArgumentParser) -> None:
    """Add OpenAPI-specific arguments to the parser.

    Args:
        parser: The ArgumentParser to add arguments to.
    """
    _add_common_arguments(parser)
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a JSON/JSONC configuration file for tools",
    )
    parser.add_argument(
        "--tokens",
        type=str,
        default=None,
        help="Path to a file containing authentication tokens (one per line)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development mode",
    )


def _add_mcp_arguments(parser: argparse.ArgumentParser) -> None:
    """Add MCP-specific arguments to the parser.

    Args:
        parser: The ArgumentParser to add arguments to.
    """
    _add_common_arguments(parser)
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type: stdio, sse, or streamable-http (default: stdio)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for SSE/HTTP transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE/HTTP transport (default: 8000)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a JSON/JSONC configuration file for tools",
    )


def main(args: list[str] | None = None) -> NoReturn | None:
    """Main entry point for the CLI.

    Args:
        args: Command-line arguments. If None, uses sys.argv.

    Returns:
        None on success, or exits with error code.
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    # Handle version flag
    if parsed.version:
        version_info = _get_version_info()
        if version_info["update_available"]:
            print(f"toolregistry-hub {version_info['current_version']}")
            print(f"Update available: v{version_info['latest_version']}")
            print("Run: pip install --upgrade toolregistry-hub")
        else:
            print(f"toolregistry-hub {version_info['current_version']} (Latest)")
        sys.exit(0)

    # If no command specified, show help
    if parsed.command is None:
        parser.print_help()
        sys.exit(0)

    # Load environment variables from .env file
    # Reuse toolregistry-server's load_env_file function
    try:
        from toolregistry_server.cli import load_env_file

        load_env_file(
            env_path=getattr(parsed, "env", None),
            no_env=getattr(parsed, "no_env", False),
        )
    except ImportError:
        logger.warning("toolregistry-server not installed, skipping .env loading")

    # Print banner unless disabled
    if not parsed.no_banner:
        print_hub_banner()

    # Apply tools config to the registry before starting the server
    if parsed.config is not None:
        from .registry import build_registry

        # Rebuild registry with the specified config path
        import toolregistry_hub.server.registry as _reg_mod

        _reg_mod._registry = build_registry(tools_config_path=parsed.config)

    # Dispatch to appropriate command handler
    admin_port = getattr(parsed, "admin_port", None)

    if parsed.command == "openapi":
        _run_openapi_server(
            host=parsed.host,
            port=parsed.port,
            tokens_path=getattr(parsed, "tokens", None),
            reload=getattr(parsed, "reload", False),
            admin_port=admin_port,
        )
    elif parsed.command == "mcp":
        _run_mcp_server(
            transport=parsed.transport,
            host=parsed.host,
            port=parsed.port,
            admin_port=admin_port,
        )

    return None


def _enable_admin_panel(registry: "ToolRegistry", port: int) -> None:
    """Enable the admin panel and execution logging on the registry.

    Args:
        registry: The ToolRegistry instance.
        port: Port number for the admin panel.
    """
    registry.enable_logging()
    info = registry.enable_admin(port=port)
    logger.info(f"Admin panel enabled at {info.url}")


def _run_openapi_server(
    host: str,
    port: int,
    tokens_path: str | None = None,
    reload: bool = False,
    admin_port: int | None = None,
) -> None:
    """Run the OpenAPI server.

    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
        tokens_path: Path to tokens file for authentication.
        reload: Enable auto-reload for development.
    """
    try:
        import uvicorn

        from toolregistry_server import RouteTable
        from toolregistry_server.auth import BearerTokenAuth, create_bearer_dependency
        from toolregistry_server.openapi import create_openapi_app
    except ImportError as e:
        logger.error(f"OpenAPI server dependencies not installed: {e}")
        logger.info("Installation options:")
        logger.info("  OpenAPI only: pip install toolregistry-hub[server_openapi]")
        logger.info("  Full server:  pip install toolregistry-hub[server]")
        sys.exit(1)

    from .auth import get_valid_tokens
    from .registry import get_registry
    from .routes.version import router as version_router

    # Log server info
    logger.info("Server mode: OpenAPI")

    # Get the hub registry
    registry = get_registry()

    # Enable admin panel if requested
    if admin_port is not None:
        _enable_admin_panel(registry, admin_port)

    # Create route table from registry
    route_table = RouteTable(registry)

    # Setup authentication
    valid_tokens = get_valid_tokens(tokens_path)
    dependencies = None

    if valid_tokens:
        auth = BearerTokenAuth(tokens=list(valid_tokens))
        dependency = create_bearer_dependency(auth)
        from fastapi import Depends

        dependencies = [Depends(dependency)]
        logger.info("Token authentication enabled for OpenAPI server")
    else:
        logger.info(
            "No tokens configured - OpenAPI server running without authentication"
        )

    # Create the OpenAPI app using toolregistry-server
    app = create_openapi_app(
        route_table,
        title="ToolRegistry-Hub Server",
        version=__version__,
        description="A server for accessing various tools like calculators, "
        "unit converters, and web search engines.",
        dependencies=dependencies,
    )

    # Add hub-specific routes (version endpoint)
    app.include_router(version_router)
    logger.info("Included version router at /version")

    logger.info("OpenAPI app initialized with toolregistry-server")
    logger.info(f"Registered {len(route_table.list_routes())} tool(s)")

    # Run the server
    if reload:
        logger.warning("Reload mode is not fully supported with dynamic configuration")

    uvicorn.run(app, host=host, port=port, reload=reload)


def _run_mcp_server(
    host: str, port: int, transport: str, admin_port: int | None = None
) -> None:
    """Run the MCP server.

    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
        transport: MCP transport type ('stdio', 'sse', or 'streamable-http').
    """
    try:
        from toolregistry_server import RouteTable
        from toolregistry_server.mcp import (
            create_mcp_server,
            run_sse,
            run_stdio,
            run_streamable_http,
        )
    except ImportError as e:
        logger.error(f"MCP server dependencies not installed: {e}")
        logger.info("Installation options:")
        logger.info(
            "  MCP only:    pip install toolregistry-hub[server_mcp] (requires Python 3.10+)"
        )
        logger.info(
            "  Full server: pip install toolregistry-hub[server] (requires Python 3.10+)"
        )
        sys.exit(1)

    import asyncio

    from .registry import get_registry

    # Log server info
    logger.info(f"Server mode: MCP (transport: {transport})")

    # Get the hub registry
    registry = get_registry()

    # Enable admin panel if requested
    if admin_port is not None:
        _enable_admin_panel(registry, admin_port)

    # Create route table from registry
    route_table = RouteTable(registry)

    # Create MCP server using toolregistry-server
    mcp_server = create_mcp_server(route_table, name="ToolRegistry-Hub")

    logger.info("MCP server initialized with toolregistry-server")
    logger.info(f"Registered {len(route_table.list_routes())} tool(s)")

    # Run the appropriate transport
    if transport == "stdio":
        asyncio.run(run_stdio(mcp_server))
    elif transport == "sse":
        logger.info(f"SSE endpoint: http://{host}:{port}/sse")
        asyncio.run(run_sse(mcp_server, host=host, port=port))
    else:  # streamable-http
        logger.info(f"HTTP endpoint: http://{host}:{port}/mcp")
        asyncio.run(run_streamable_http(mcp_server, host=host, port=port))


if __name__ == "__main__":
    main()
