"""Core server implementation without authentication.

This module provides the base FastAPI application with all routes
but without any authentication middleware. It serves as the foundation
for both OpenAPI and MCP server implementations.
"""

from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger

from ..__init__ import version
from .autoroute import registry_to_router, setup_dynamic_openapi
from .registry import get_registry
from .routes.version import router as version_router

# Load environment variables
load_dotenv()


def create_core_app(dependencies: Optional[List[Any]] = None) -> FastAPI:
    """Create the core FastAPI application without authentication.

    Args:
        dependencies: Optional list of dependencies, for example, token authentication logic

    Returns:
        FastAPI application instance with all routes but no auth
    """

    title = "ToolRegistry-Hub Core Server"
    description = "Core API for accessing various tools like calculators, unit converters, and web search engines."

    if dependencies:
        app = FastAPI(
            title=title,
            description=description,
            version=version,
            dependencies=dependencies,
        )
    else:
        app = FastAPI(
            title=title,
            description=description,
            version=version,
        )

    # Registry-driven auto-generated routes
    registry = get_registry()
    auto_router = registry_to_router(registry, prefix="/tools")
    app.include_router(auto_router)
    logger.info(
        f"Included auto-generated router with {len(auto_router.routes)} routes at /tools"
    )

    # Version metadata route
    app.include_router(version_router)
    logger.info("Included version router at /version")

    # Dynamic OpenAPI: hide disabled tools from /docs and /openapi.json
    setup_dynamic_openapi(app, registry)

    logger.info("Core FastAPI app initialized with auto-routes and version router")
    return app


def set_info(mode: str, mcp_transport: Optional[str] = None) -> None:
    """Set server information for logging purposes.

    Args:
        mode: Server mode ('openapi', 'mcp', or 'core')
        mcp_transport: MCP transport mode (only used when mode is 'mcp')
    """
    if mode == "core":
        logger.info("Server mode: Core (no authentication)")
    elif mode == "openapi":
        logger.info("Server mode: OpenAPI")
    elif mode == "mcp":
        transport_info = mcp_transport or "default"
        logger.info(f"Server mode: MCP (transport: {transport_info})")
    else:
        logger.warning(f"Unknown server mode: {mode}")
