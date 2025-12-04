"""MCP server implementation with FastMCP authentication.

This module provides an MCP server with proper token verification
using FastMCP's DebugTokenVerifier.
"""

from fastmcp import FastMCP
from fastmcp.server.auth.providers.debug import DebugTokenVerifier
from loguru import logger

from .auth import get_valid_tokens
from .server_core import create_core_app


def token_validator(token: str) -> bool:
    """Validate token using our existing auth logic.

    Args:
        token: Bearer token to verify

    Returns:
        True if token is valid, False otherwise
    """
    valid_tokens = get_valid_tokens()

    # If no tokens configured, allow all requests
    if not valid_tokens:
        logger.debug("No tokens configured - allowing all requests")
        return True

    if token in valid_tokens:
        logger.debug(f"Authenticated MCP request with token: {token[:8]}...")
        return True

    logger.warning(f"Invalid MCP token attempt: {token[:8]}...")
    return False


def create_mcp_app() -> FastMCP:
    """Create MCP FastMCP application with authentication.

    Returns:
        FastMCP application with token authentication
    """
    valid_tokens = get_valid_tokens()

    if valid_tokens:
        logger.info("Token authentication enabled for MCP server")
    else:
        logger.info("No tokens configured - MCP server running without authentication")

    # Always create with DebugTokenVerifier - it will handle the no-tokens case internally
    auth = DebugTokenVerifier(validate=token_validator)
    mcp_app = FastMCP.from_fastapi(
        create_core_app(),
        name="ToolRegistry-Hub MCP Server",
        auth=auth,
    )

    logger.info("MCP FastMCP app initialized")
    return mcp_app


# Create the MCP app instance
mcp_app = create_mcp_app()
