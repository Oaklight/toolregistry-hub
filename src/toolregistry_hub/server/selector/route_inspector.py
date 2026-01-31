"""Route inspector for discovering and analyzing tools."""

import hashlib
from typing import Dict, List, Any
from fastapi import APIRouter
from loguru import logger

from ..routes import discover_routers
from .models import ToolConfig, ToolEndpoint, ToolRegistry


class RouteInspector:
    """Route inspector - discovers tools based on existing discover_routers() mechanism."""
    
    def __init__(self):
        self.discovered_routers: List[APIRouter] = []
        self.tool_registry = ToolRegistry()
    
    def discover_tools(self) -> Dict[str, Any]:
        """Discover all available tools using the existing route discovery mechanism."""
        try:
            logger.info("Starting tool discovery...")
            self.discovered_routers = discover_routers()
            self.tool_registry.tools = self._extract_tool_info()
            logger.info(f"Discovered {len(self.tool_registry.tools)} tools")
            return self._serialize_tools()
        except Exception as e:
            logger.error(f"Error during tool discovery: {e}")
            return {}
    
    def _extract_tool_info(self) -> Dict[str, ToolConfig]:
        """Extract tool information from discovered routers."""
        tools = {}
        
        for router in self.discovered_routers:
            try:
                tool_id = self._get_tool_id(router)
                tool_config = ToolConfig(
                    id=tool_id,
                    name=self._get_tool_name(router),
                    prefix=router.prefix or "/",
                    tags=list(router.tags) if router.tags else [],
                    endpoints=self._extract_endpoints(router),
                    module_name=self._get_module_name(router),
                    description=self._get_tool_description(router)
                )
                tools[tool_id] = tool_config
                logger.debug(f"Extracted tool: {tool_id}")
            except Exception as e:
                logger.warning(f"Failed to extract tool info from router: {e}")
        
        return tools
    
    def _get_tool_id(self, router: APIRouter) -> str:
        """Generate a unique tool ID from router information."""
        # Use prefix and tags to generate a unique ID
        prefix = router.prefix or "root"
        tags = "-".join(sorted(router.tags)) if router.tags else "notag"
        
        # Create a hash for uniqueness
        content = f"{prefix}-{tags}"
        tool_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Make it more readable
        if router.prefix:
            clean_prefix = router.prefix.strip("/").replace("/", "_")
            return f"{clean_prefix}_{tool_id}"
        elif router.tags:
            return f"{list(router.tags)[0]}_{tool_id}"
        else:
            return f"tool_{tool_id}"
    
    def _get_tool_name(self, router: APIRouter) -> str:
        """Get a human-readable tool name."""
        if router.tags:
            # Use the first tag as the name, capitalize it
            return list(router.tags)[0].title()
        elif router.prefix:
            # Use prefix without slashes, capitalize
            return router.prefix.strip("/").replace("/", " ").title()
        else:
            return "Unknown Tool"
    
    def _get_tool_description(self, router: APIRouter) -> str:
        """Get tool description from router or routes."""
        # Try to get description from the first route's docstring
        for route in router.routes:
            if hasattr(route, 'endpoint') and route.endpoint:
                if hasattr(route.endpoint, '__doc__') and route.endpoint.__doc__:
                    return route.endpoint.__doc__.strip().split('\n')[0]
        
        # Fallback to tags or prefix
        if router.tags:
            return f"API endpoints for {list(router.tags)[0]}"
        elif router.prefix:
            return f"API endpoints for {router.prefix.strip('/')}"
        else:
            return "API endpoints"
    
    def _get_module_name(self, router: APIRouter) -> str:
        """Get the module name where the router is defined."""
        # Try to get module name from the first route's endpoint
        for route in router.routes:
            if hasattr(route, 'endpoint') and route.endpoint:
                if hasattr(route.endpoint, '__module__'):
                    return route.endpoint.__module__
        return "unknown"
    
    def _extract_endpoints(self, router: APIRouter) -> List[ToolEndpoint]:
        """Extract endpoint information from a router."""
        endpoints = []
        
        for route in router.routes:
            try:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    endpoint = ToolEndpoint(
                        path=route.path,
                        methods=list(route.methods) if route.methods else [],
                        name=getattr(route, 'name', ''),
                        summary=getattr(route, 'summary', ''),
                        operation_id=getattr(route, 'operation_id', '')
                    )
                    endpoints.append(endpoint)
            except Exception as e:
                logger.warning(f"Failed to extract endpoint info: {e}")
        
        return endpoints
    
    def _serialize_tools(self) -> Dict[str, Any]:
        """Serialize tools for JSON response."""
        return {
            tool_id: {
                "id": tool.id,
                "name": tool.name,
                "prefix": tool.prefix,
                "enabled": tool.enabled,
                "description": tool.description,
                "tags": tool.tags,
                "endpoints": [
                    {
                        "path": ep.path,
                        "methods": ep.methods,
                        "name": ep.name,
                        "summary": ep.summary,
                        "operation_id": ep.operation_id
                    }
                    for ep in tool.endpoints
                ],
                "module_name": tool.module_name,
                "endpoint_count": len(tool.endpoints)
            }
            for tool_id, tool in self.tool_registry.tools.items()
        }
    
    def get_tool_by_id(self, tool_id: str) -> ToolConfig:
        """Get a specific tool by ID."""
        return self.tool_registry.tools.get(tool_id)
    
    def get_all_tools(self) -> Dict[str, ToolConfig]:
        """Get all discovered tools."""
        return self.tool_registry.tools
    
    def reload_tools(self) -> Dict[str, Any]:
        """Reload all tools by re-discovering routes."""
        logger.info("Reloading tools...")
        
        # Clear existing data
        self.discovered_routers.clear()
        self.tool_registry.tools.clear()
        
        # Re-discover
        return self.discover_tools()