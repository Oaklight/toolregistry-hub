import argparse
import sys

from loguru import logger

from .. import __version__
from ..version_check import check_for_updates, get_version_check_sync
from .banner import BANNER_ART
from .server_core import set_info


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


def main():
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
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {get_version_check_sync()}",
        help="Show the version and check for updates",
    )
    args = parser.parse_args()

    if args.mode == "openapi":
        try:
            import uvicorn

            from .server_openapi import app
        except ImportError as e:
            logger.error(f"OpenAPI server dependencies not installed: {e}")
            logger.info("Installation options:")
            logger.info(
                "  OpenAPI only: pip install toolregistry-hub[server_openapi] (requires Python 3.8+)"
            )
            logger.info(
                "  All server modes: pip install toolregistry-hub[server] (requires Python 3.10+)"
            )
            sys.exit(1)

        # Set server info
        set_info(mode="openapi")
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.mode == "mcp":
        try:
            from .server_mcp import mcp_app
        except ImportError as e:
            logger.error(f"MCP server dependencies not installed: {e}")
            logger.info("Installation options:")
            logger.info(
                "  MCP only: pip install toolregistry-hub[server_mcp] (requires Python 3.10+)"
            )
            logger.info(
                "  All server modes: pip install toolregistry-hub[server] (requires Python 3.10+)"
            )
            sys.exit(1)

        # Set server info
        set_info(mode="mcp", mcp_transport=args.mcp_transport)

        if args.mcp_transport == "stdio":
            mcp_app.run(
                show_banner=False
            )  # Run MCP in stdio mode; assumes FastMCP supports this method
        else:
            mcp_app.run(
                transport=args.mcp_transport,
                host=args.host,
                port=args.port,
                show_banner=False,
            )


if __name__ == "__main__":
    main()
