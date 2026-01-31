from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from loguru import logger

from ..__init__ import version
from .dynamic_router import DynamicRouterManager
from .routes import get_all_routers

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ToolRegistry-Hub OpenAPI Server",
    description="An API for accessing various tools like calculators, unit converters, and web search engines.",
    version=version,
)

# Initialize dynamic router manager
dynamic_router_manager = DynamicRouterManager(app)

# Initialize with discovered tools
discovered_tools = dynamic_router_manager.initialize()
logger.info("FastAPI app initialized with dynamic router manager")
logger.info(f"Discovered {len(discovered_tools)} tools")


internal = APIRouter(prefix="/internal", tags=["internal", "control"])


# Add internal API endpoints for selector communication
@internal.post("/tools/{tool_id}/toggle")
async def toggle_tool_internal(tool_id: str):
    """Internal API endpoint for toggling tool state."""
    try:
        # Get current state
        current_status = dynamic_router_manager.get_tool_status()
        current_enabled = current_status.get(tool_id, False)

        # Toggle the tool
        if current_enabled:
            success = dynamic_router_manager.disable_tool(tool_id)
            new_state = False
        else:
            success = dynamic_router_manager.enable_tool(tool_id)
            new_state = True

        if success:
            return {
                "success": True,
                "message": f"Tool {tool_id} {'enabled' if new_state else 'disabled'} successfully",
                "tool_id": tool_id,
                "enabled": new_state,
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Failed to toggle tool {tool_id}"
            )

    except Exception as e:
        logger.error(f"Error toggling tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@internal.post("/server/reload")
async def reload_server_internal():
    """Internal API endpoint for reloading server tools."""
    try:
        discovered_tools = dynamic_router_manager.reload_tools()
        
        app.openapi_schema = None
        app.setup()
        return {
            "success": True,
            "message": "Server reloaded successfully",
            "tools_discovered": len(discovered_tools),
        }
    except Exception as e:
        logger.error(f"Error reloading server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@internal.get("/tools/status")
async def get_tools_status_internal():
    """Internal API endpoint for getting tools status."""
    try:
        status = dynamic_router_manager.get_tool_status()
        enabled_count = sum(1 for enabled in status.values() if enabled)

        return {
            "tools": status,
            "total_count": len(status),
            "enabled_count": enabled_count,
        }
    except Exception as e:
        logger.error(f"Error getting tools status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@internal.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "toolregistry-hub", "version": version}


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


def invalidate_cache():
    app.openapi_schema = None;
    app.setup()

app.include_router(internal, include_in_schema=False)
