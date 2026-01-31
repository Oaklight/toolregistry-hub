"""Selector server application."""

import json
from pathlib import Path
from typing import Dict, Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

from .models import ToggleResponse, ServerStatusResponse, ReloadResponse
from .route_inspector import RouteInspector


class SelectorApp:
    """Selector server application."""
    
    def __init__(self, main_server_url: str = "http://localhost:8000"):
        self.app = FastAPI(
            title="ToolRegistry-Hub Selector",
            description="Tool selector interface for ToolRegistry-Hub",
            version="1.0.0"
        )
        self.main_server_url = main_server_url
        self.route_inspector = RouteInspector()
        
        self.setup_static_files()
        self.setup_routes()
        
        logger.info(f"Selector app initialized, main server: {main_server_url}")
    
    def setup_static_files(self):
        """Setup static file serving."""
        static_path = Path(__file__).parent / "static"
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
            logger.info(f"Static files mounted from: {static_path}")
        else:
            logger.warning(f"Static directory not found: {static_path}")
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """Serve the main selector interface."""
            try:
                static_path = Path(__file__).parent / "static" / "index.html"
                if static_path.exists():
                    return HTMLResponse(content=static_path.read_text(encoding='utf-8'))
                else:
                    return HTMLResponse(
                        content="<h1>Selector Interface</h1><p>Static files not found</p>",
                        status_code=200
                    )
            except Exception as e:
                logger.error(f"Error serving index page: {e}")
                return HTMLResponse(
                    content=f"<h1>Error</h1><p>Failed to load interface: {e}</p>",
                    status_code=500
                )
        
        @self.app.get("/api/tools")
        async def get_tools():
            """Get all discovered tools."""
            try:
                tools = self.route_inspector.discover_tools()
                return JSONResponse(content=tools)
            except Exception as e:
                logger.error(f"Error getting tools: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/tools/{tool_id}/toggle")
        async def toggle_tool(tool_id: str):
            """Toggle a tool's enabled state."""
            try:
                # For now, we'll simulate the toggle since we haven't implemented
                # the main server integration yet
                logger.info(f"Toggle tool request: {tool_id}")
                
                # Try to communicate with main server
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.post(
                            f"{self.main_server_url}/internal/tools/{tool_id}/toggle"
                        )
                        if response.status_code == 200:
                            result = response.json()
                            return ToggleResponse(
                                success=result.get("success", True),
                                message=result.get("message", "Tool toggled successfully"),
                                tool_id=tool_id,
                                enabled=result.get("enabled", True)
                            )
                except httpx.RequestError:
                    logger.warning("Main server not available, simulating toggle")
                
                # Simulate successful toggle for now
                return ToggleResponse(
                    success=True,
                    message=f"Tool {tool_id} toggled successfully (simulated)",
                    tool_id=tool_id,
                    enabled=True
                )
                
            except Exception as e:
                logger.error(f"Error toggling tool {tool_id}: {e}")
                return ToggleResponse(
                    success=False,
                    message=str(e),
                    tool_id=tool_id,
                    enabled=False
                )
        
        @self.app.post("/api/server/reload")
        async def reload_server():
            """Reload the main server and rediscover tools."""
            try:
                logger.info("Server reload request")
                
                # Try to communicate with main server
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{self.main_server_url}/internal/server/reload"
                        )
                        if response.status_code == 200:
                            result = response.json()
                            return ReloadResponse(
                                success=result.get("success", True),
                                message=result.get("message", "Server reloaded successfully"),
                                tools_discovered=result.get("tools_discovered", 0)
                            )
                except httpx.RequestError:
                    logger.warning("Main server not available, reloading locally")
                
                # Reload tools locally
                tools = self.route_inspector.reload_tools()
                tools_count = len(tools)
                
                return ReloadResponse(
                    success=True,
                    message=f"Tools reloaded successfully (local reload)",
                    tools_discovered=tools_count
                )
                
            except Exception as e:
                logger.error(f"Error reloading server: {e}")
                return ReloadResponse(
                    success=False,
                    message=str(e),
                    tools_discovered=0,
                    errors=[str(e)]
                )
        
        @self.app.get("/api/tools/status")
        async def get_tools_status():
            """Get tools status and server health."""
            try:
                tools = self.route_inspector.get_all_tools()
                tools_count = len(tools)
                enabled_count = sum(1 for tool in tools.values() if tool.enabled)
                
                # Check main server health
                server_online = False
                try:
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        response = await client.get(f"{self.main_server_url}/health")
                        server_online = response.status_code == 200
                except httpx.RequestError:
                    pass
                
                return ServerStatusResponse(
                    online=server_online,
                    tools_count=tools_count,
                    enabled_count=enabled_count
                )
                
            except Exception as e:
                logger.error(f"Error getting tools status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "selector"}
        
        # Add CORS middleware for development
        @self.app.middleware("http")
        async def add_cors_header(request, call_next):
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response


def create_selector_app(main_server_url: str = "http://localhost:8000") -> FastAPI:
    """Create and configure the selector application."""
    selector = SelectorApp(main_server_url)
    return selector.app


# For direct usage
if __name__ == "__main__":
    import uvicorn
    
    app = create_selector_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)