"""Core server implementation without authentication.

This module provides the base FastAPI application with all routes
but without any authentication middleware. It serves as the foundation
for both OpenAPI and MCP server implementations.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger

from ..__init__ import version
from .routes import get_all_routers

# Load environment variables
load_dotenv()


def create_core_app() -> FastAPI:
    """Create the core FastAPI application without authentication.

    Returns:
        FastAPI application instance with all routes but no auth
    """
    app = FastAPI(
        title="ToolRegistry-Hub Core Server",
        description="Core API for accessing various tools like calculators, unit converters, and web search engines.",
        version=version,
    )

    # Automatically discover and include all routers
    routers = get_all_routers()
    for router in routers:
        app.include_router(router)
        logger.info(f"Included router with prefix: {router.prefix or '/'}")

    logger.info(f"Core FastAPI app initialized with {len(routers)} routers")
    return app
