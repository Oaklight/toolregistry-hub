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
from .routes import get_all_routers

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

    # New: registry-driven auto-generated routes (Phase 5)
    registry = get_registry()
    auto_router = registry_to_router(registry, prefix="/tools")
    app.include_router(auto_router)
    logger.info(
        f"Included auto-generated router with {len(auto_router.routes)} routes at /tools"
    )

    # Legacy: keep existing hand-written routes during migration (removed in Phase 8)
    routers = get_all_routers()
    for router in routers:
        app.include_router(router)
        logger.info(f"Included legacy router with prefix: {router.prefix or '/'}")

    # Dynamic OpenAPI: hide disabled tools from /docs and /openapi.json
    setup_dynamic_openapi(app, registry)

    logger.info(
        f"Core FastAPI app initialized with auto-routes + {len(routers)} legacy routers"
    )
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
