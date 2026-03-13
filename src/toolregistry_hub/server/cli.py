"""Command-line interface for ToolRegistry Hub Server.

This module provides the CLI entry point for running ToolRegistry Hub servers
with support for both OpenAPI and MCP protocols.

Usage:
    toolregistry-server [OPTIONS]
    toolregistry-server --help

Example:
    # Start OpenAPI server on port 8000
    $ toolregistry-server --port 8000

    # Start MCP server with stdio transport
    $ toolregistry-server --mode mcp --mcp-transport stdio

    # Start MCP server with SSE transport
    $ toolregistry-server --mode mcp --mcp-transport sse --port 8000

    # With configuration file
    $ toolregistry-server --tools-config tools.jsonc
"""

import argparse
import sys

from loguru import logger

from .. import __version__
from ..version_check import check_for_updates, get_version_check_sync
from .banner import BANNER_ART


def print_banner():
    """Print the ToolRegistry Hub banner with centered content and border."""
    import asyncio

    width = 80
    border_char = "·"

    # Split banner art into lines
    art_lines = BANNER_ART.split("\n")

    # Check for updates
    try:
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, skip async version check
            logger.debug(
                "Already in event loop, skipping async version check in banner"
            )
            version_info = {
                "current_version": __version__,
                "update_available": False,
                "latest_version": None,
            }
        except RuntimeError:
            # No running loop, safe to create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                version_info = loop.run_until_complete(check_for_updates())
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    except Exception as e:
        logger.debug(f"Failed to check for updates in banner: {e}")
        version_info = {
            "current_version": __version__,
            "update_available": False,
            "latest_version": None,
        }

    # Build the banner
    lines = []

    # Top border
    lines.append(border_char * width)

    # Empty line
    lines.append(f": {' ' * (width - 4)} :")

    # Art lines - center each line
    for line in art_lines:
        centered = line.center(width - 4)
        lines.append(f": {centered} :")

    # Empty line
    lines.append(f": {' ' * (width - 4)} :")

    # Version information with update status
    if version_info["update_available"]:
        version_line = f"Version {version_info['current_version']}"
        update_line = f"UPDATE AVAILABLE: v{version_info['latest_version']}"
        install_line = "Run: pip install --upgrade toolregistry-hub"

        # Center and add version lines
        centered_version = version_line.center(width - 4)
        lines.append(f": {centered_version} :")

        centered_update = update_line.center(width - 4)
        lines.append(f": {centered_update} :")

        centered_install = install_line.center(width - 4)
        lines.append(f": {centered_install} :")
    else:
        version_line = f"Version {version_info['current_version']} (Latest)"
        centered_version = version_line.center(width - 4)
        lines.append(f": {centered_version} :")

    # Empty line
    lines.append(f": {' ' * (width - 4)} :")

    # Bottom border
    lines.append(border_char * width)

    # Print the banner
    print("\n".join(lines))


def _log_server_info(mode: str, mcp_transport: str | None = None) -> None:
    """Log server information for logging purposes.

    Args:
        mode: Server mode ('openapi' or 'mcp')
        mcp_transport: MCP transport mode (only used when mode is 'mcp')
    """
    if mode == "openapi":
        logger.info("Server mode: OpenAPI")
    elif mode == "mcp":
        transport_info = mcp_transport or "default"
        logger.info(f"Server mode: MCP (transport: {transport_info})")
    else:
        logger.warning(f"Unknown server mode: {mode}")


def main():
    """Main entry point for the CLI."""
    # Print banner at startup
    print_banner()

    parser = argparse.ArgumentParser(description="Run the Tool Registry API server.")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to. Default is 0.0.0.0.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to. Default is 8000.",
    )
    parser.add_argument(
        "--mode",
        choices=["openapi", "mcp"],
        default="openapi",
        help="Server mode: openapi or mcp. Default is openapi.",
    )
    parser.add_argument(
        "--mcp-transport",
        choices=["streamable-http", "sse", "stdio"],
        default="streamable-http",
        help="MCP transport mode for mcp mode. Default is streamable-http.",
    )
    parser.add_argument(
        "--tools-config",
        type=str,
        default=None,
        help="Path to a JSONC tool configuration file (tools.jsonc). "
        "Controls which tools are enabled/disabled at startup.",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {get_version_check_sync()}",
        help="Show the version and check for updates",
    )
    args = parser.parse_args()

    # Apply tools config to the registry before starting the server
    if args.tools_config is not None:
        from .registry import build_registry

        # Rebuild registry with the specified config path
        import toolregistry_hub.server.registry as _reg_mod

        _reg_mod._registry = build_registry(tools_config_path=args.tools_config)

    if args.mode == "openapi":
        _run_openapi_server(args.host, args.port)
    elif args.mode == "mcp":
        _run_mcp_server(args.host, args.port, args.mcp_transport)


def _run_openapi_server(host: str, port: int) -> None:
    """Run the OpenAPI server.

    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
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
    _log_server_info(mode="openapi")

    # Get the hub registry
    registry = get_registry()

    # Create route table from registry
    route_table = RouteTable(registry)

    # Setup authentication
    valid_tokens = get_valid_tokens()
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

    # Run the server
    uvicorn.run(app, host=host, port=port)


def _run_mcp_server(host: str, port: int, transport: str) -> None:
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
    _log_server_info(mode="mcp", mcp_transport=transport)

    # Get the hub registry
    registry = get_registry()

    # Create route table from registry
    route_table = RouteTable(registry)

    # Create MCP server using toolregistry-server
    mcp_server = create_mcp_server(route_table, name="ToolRegistry-Hub")

    logger.info("MCP server initialized with toolregistry-server")

    # Run the appropriate transport
    if transport == "stdio":
        asyncio.run(run_stdio(mcp_server))
    elif transport == "sse":
        asyncio.run(run_sse(mcp_server, host=host, port=port))
    else:  # streamable-http
        asyncio.run(run_streamable_http(mcp_server, host=host, port=port))


if __name__ == "__main__":
    main()
