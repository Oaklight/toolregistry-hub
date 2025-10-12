from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger

from ..__init__ import version
from .routes import get_all_routers

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ToolRegistry-Hub OpenAPI Server",
    description="An API for accessing various tools like calculators, unit converters, and web search engines.",
    version=version,
)

# Automatically discover and include all routers
routers = get_all_routers()
for router in routers:
    app.include_router(router)
    logger.info(f"Included router with prefix: {router.prefix or '/'}")

logger.info(f"FastAPI app initialized with {len(routers)} routers")


def set_info(mode: str, mcp_transport: Optional[str] = None) -> None:
    """Set server information for logging purposes.

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
