import argparse
import sys

from loguru import logger

from .server_core import set_info


def main():
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
            mcp_app.run()  # Run MCP in stdio mode; assumes FastMCP supports this method
        else:
            mcp_app.run(transport=args.mcp_transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
