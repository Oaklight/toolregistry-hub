"""MCP server implementation using FastMCP from the MCP SDK.

This module provides functions to create and run an MCP server backed by
a ToolRegistry, supporting stdio, SSE, and streamable-http transports.
"""

import asyncio
import json
import os
import signal
import sys
from typing import Any

from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData
from toolregistry import ToolRegistry


def create_mcp_server(
    registry: ToolRegistry, name: str = "ToolRegistry-Hub"
) -> FastMCP:
    """Create a FastMCP server from the given registry.

    Args:
        registry: The ToolRegistry instance to expose as MCP tools.
        name: The name of the MCP server.

    Returns:
        A configured FastMCP instance.
    """
    mcp = FastMCP(name)

    # Store registry reference for runtime checks
    mcp._registry = registry  # type: ignore[attr-defined]

    # Dynamically register all tools from the registry
    for tool_name in registry.list_tools():
        tool = registry.get_tool(tool_name)
        if tool is None:
            continue

        # Create a closure to capture the tool name and registry
        def make_tool_handler(t_name: str, reg: ToolRegistry):
            async def tool_handler(**kwargs: Any) -> str:
                """Execute the tool with the given arguments."""
                # Check if tool is disabled at call time
                if not reg.is_enabled(t_name):
                    reason = reg.get_disable_reason(t_name) or "unknown reason"
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Tool '{t_name}' is disabled: {reason}",
                        )
                    )

                t = reg.get_tool(t_name)
                if t is None:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Tool '{t_name}' not found",
                        )
                    )

                try:
                    if t.is_async:
                        result = await t.arun(kwargs)
                    else:
                        result = t.run(kwargs)

                    # Serialize result to text
                    if isinstance(result, (dict, list)):
                        return json.dumps(result, ensure_ascii=False, default=str)
                    else:
                        return str(result)

                except McpError:
                    raise
                except Exception as e:
                    logger.warning(f"call_tool '{t_name}': error - {e}")
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=str(e),
                        )
                    )

            return tool_handler

        # Register the tool with FastMCP
        handler = make_tool_handler(tool_name, registry)
        handler.__name__ = tool_name
        handler.__doc__ = tool.description or f"Execute {tool_name}"

        # Use the tool decorator to register
        mcp.tool(name=tool_name, description=tool.description or "")(handler)

    logger.info("MCP server created from ToolRegistry")
    return mcp


async def run_mcp_stdio(mcp: FastMCP) -> None:
    """Run MCP server over stdio transport.

    Args:
        mcp: The FastMCP instance to run.
    """
    logger.info("Starting MCP server with stdio transport")
    try:
        # Use the async version directly to avoid nested event loop issues
        # mcp.run() is synchronous and calls anyio.run() internally
        await mcp.run_stdio_async()
    except KeyboardInterrupt:
        logger.info("MCP stdio server shutdown requested (KeyboardInterrupt)")
    except asyncio.CancelledError:
        logger.info("MCP stdio server shutdown requested (CancelledError)")


async def run_mcp_http(
    mcp: FastMCP,
    host: str,
    port: int,
    transport_type: str = "streamable-http",
) -> None:
    """Run MCP server over HTTP transport (streamable-http or sse).

    Args:
        mcp: The FastMCP instance to run.
        host: Host address to bind to.
        port: Port number to bind to.
        transport_type: Transport type, either ``"streamable-http"`` or ``"sse"``.

    Raises:
        ValueError: If an unsupported transport type is specified.
    """
    if transport_type not in ("streamable-http", "sse"):
        raise ValueError(f"Unsupported MCP transport type: {transport_type}")

    logger.info(f"Starting MCP server with {transport_type} transport on {host}:{port}")

    # FastMCP uses environment variables for host/port configuration
    # Set them before calling the async methods so the server binds to the correct address
    os.environ["FASTMCP_HOST"] = host
    os.environ["FASTMCP_PORT"] = str(port)

    # Set up graceful shutdown handling
    shutdown_event = asyncio.Event()

    def _signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        shutdown_event.set()

    # Install signal handlers for graceful shutdown
    # Only install on Unix-like systems; Windows handles signals differently
    if sys.platform != "win32":
        original_sigint = signal.signal(signal.SIGINT, _signal_handler)
        original_sigterm = signal.signal(signal.SIGTERM, _signal_handler)

    try:
        # Use the async versions directly to avoid nested event loop issues
        # mcp.run() is synchronous and calls anyio.run() internally, which causes
        # "RuntimeError: Already running asyncio in this thread" when called from
        # within an existing async context
        if transport_type == "sse":
            await mcp.run_sse_async()
        else:
            await mcp.run_streamable_http_async()
    except KeyboardInterrupt:
        logger.info("MCP HTTP server shutdown requested (KeyboardInterrupt)")
    except asyncio.CancelledError:
        logger.info("MCP HTTP server shutdown requested (CancelledError)")
    except SystemExit:
        logger.info("MCP HTTP server shutdown requested (SystemExit)")
    finally:
        # Restore original signal handlers
        if sys.platform != "win32":
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
        logger.info("MCP HTTP server stopped")
