"""Dynamic router manager for controlling tool routes at runtime."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, List, Any, Optional

from fastapi import FastAPI, APIRouter
from loguru import logger

from .routes import discover_routers
from .selector.models import ToolConfig, ToolRegistry
from .selector.route_inspector import RouteInspector


class DynamicRouterManager:
    """Dynamic router manager - controls route enabling/disabling at runtime."""
    
    def __init__(self, app: FastAPI, config_file: str = "config/tools_config.json"):
        self.app = app
        self.config_file = Path(config_file)
        self.all_routers: Dict[str, APIRouter] = {}
        self.enabled_tools: Set[str] = set()
        self.route_inspector = RouteInspector()
        self.tool_registry = ToolRegistry()
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Dynamic router manager initialized")
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize the router manager - discover and register routes."""
        try:
            logger.info("Initializing dynamic router manager...")
            
            # Load existing configuration
            self._load_config()
            
            # Discover all available tools
            discovered_tools = self.route_inspector.discover_tools()
            
            # Update tool registry with discovered tools
            self._update_tool_registry(discovered_tools)
            
            # Register routers for enabled tools
            self._register_enabled_routers()
            
            # Save updated configuration
            self._save_config()
            
            logger.info(f"Dynamic router manager initialized with {len(self.all_routers)} tools")
            return discovered_tools
            
        except Exception as e:
            logger.error(f"Error initializing dynamic router manager: {e}")
            return {}
    
    def enable_tool(self, tool_id: str) -> bool:
        """Enable a tool by adding its router to the app."""
        try:
            if tool_id not in self.tool_registry.tools:
                logger.warning(f"Tool {tool_id} not found in registry")
                return False
            
            if tool_id in self.enabled_tools:
                logger.info(f"Tool {tool_id} is already enabled")
                return True
            
            # Find the router for this tool
            router = self._find_router_by_tool_id(tool_id)
            if not router:
                logger.error(f"Router not found for tool {tool_id}")
                return False
            
            # Add router to app
            self.app.include_router(router)
            self.enabled_tools.add(tool_id)
            
            # Update tool config
            self.tool_registry.tools[tool_id].enabled = True
            self._save_config()
            
            logger.info(f"Tool {tool_id} enabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling tool {tool_id}: {e}")
            return False
    
    def disable_tool(self, tool_id: str) -> bool:
        """Disable a tool by removing its router from the app."""
        try:
            if tool_id not in self.enabled_tools:
                logger.info(f"Tool {tool_id} is already disabled")
                return True
            
            # FastAPI doesn't support removing routers directly,
            # so we need to rebuild the app routes
            self.enabled_tools.discard(tool_id)
            
            # Update tool config
            if tool_id in self.tool_registry.tools:
                self.tool_registry.tools[tool_id].enabled = False
            
            # Rebuild app routes
            self._rebuild_app_routes()
            self._save_config()
            
            logger.info(f"Tool {tool_id} disabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling tool {tool_id}: {e}")
            return False
    
    def reload_tools(self) -> Dict[str, Any]:
        """Reload all tools by re-discovering routes."""
        try:
            logger.info("Reloading tools...")
            
            # Clear existing data
            self.all_routers.clear()
            
            # Re-discover tools
            discovered_tools = self.route_inspector.reload_tools()
            
            # Update tool registry
            self._update_tool_registry(discovered_tools)
            
            # Rebuild app routes with current enabled state
            self._rebuild_app_routes()
            
            # Save configuration
            self._save_config()
            
            logger.info(f"Tools reloaded successfully, found {len(discovered_tools)} tools")
            return discovered_tools
            
        except Exception as e:
            logger.error(f"Error reloading tools: {e}")
            return {}
    
    def get_tool_status(self) -> Dict[str, bool]:
        """Get the enabled status of all tools."""
        return {
            tool_id: tool_id in self.enabled_tools
            for tool_id in self.tool_registry.tools.keys()
        }
    
    def get_enabled_tools(self) -> Set[str]:
        """Get the set of enabled tool IDs."""
        return self.enabled_tools.copy()
    
    def get_all_tools(self) -> Dict[str, ToolConfig]:
        """Get all discovered tools."""
        return self.tool_registry.tools
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load tool registry
                if 'tools' in data:
                    self.tool_registry = ToolRegistry(**data)
                    
                    # Load enabled tools set
                    self.enabled_tools = {
                        tool_id for tool_id, tool in self.tool_registry.tools.items()
                        if tool.enabled
                    }
                    
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.info("No existing configuration found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.tool_registry = ToolRegistry()
            self.enabled_tools = set()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Update timestamp
            self.tool_registry.last_updated = datetime.now()
            
            # Convert to dict for JSON serialization
            config_data = self.tool_registry.dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
                
            logger.debug(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def _update_tool_registry(self, discovered_tools: Dict[str, Any]) -> None:
        """Update the tool registry with discovered tools."""
        # Convert discovered tools to ToolConfig objects
        new_tools = {}
        
        for tool_id, tool_data in discovered_tools.items():
            # Check if tool already exists in registry
            if tool_id in self.tool_registry.tools:
                # Keep existing enabled state
                existing_tool = self.tool_registry.tools[tool_id]
                tool_data['enabled'] = existing_tool.enabled
            else:
                # New tool, enable by default
                tool_data['enabled'] = True
            
            # Create ToolConfig object
            try:
                # Convert endpoints data
                endpoints = []
                for ep_data in tool_data.get('endpoints', []):
                    from .selector.models import ToolEndpoint
                    endpoints.append(ToolEndpoint(**ep_data))
                
                tool_config = ToolConfig(
                    id=tool_data['id'],
                    name=tool_data['name'],
                    prefix=tool_data['prefix'],
                    enabled=tool_data['enabled'],
                    description=tool_data.get('description', ''),
                    tags=tool_data.get('tags', []),
                    endpoints=endpoints,
                    module_name=tool_data.get('module_name', '')
                )
                
                new_tools[tool_id] = tool_config
                
            except Exception as e:
                logger.error(f"Error creating ToolConfig for {tool_id}: {e}")
        
        # Update registry
        self.tool_registry.tools = new_tools
        
        # Update enabled tools set
        self.enabled_tools = {
            tool_id for tool_id, tool in new_tools.items()
            if tool.enabled
        }
    
    def _register_enabled_routers(self) -> None:
        """Register routers for enabled tools."""
        # Discover all routers
        all_routers = discover_routers()
        
        # Map routers to tool IDs
        for router in all_routers:
            tool_id = self._get_tool_id_from_router(router)
            if tool_id:
                self.all_routers[tool_id] = router
                
                # Include router if tool is enabled
                if tool_id in self.enabled_tools:
                    self.app.include_router(router)
                    logger.debug(f"Registered router for enabled tool: {tool_id}")
    
    def _rebuild_app_routes(self) -> None:
        """Rebuild app routes with only enabled tools."""
        try:
            # Clear existing routes (keep non-tool routes)
            original_routes = []
            for route in self.app.router.routes:
                # Keep routes that don't belong to tools
                if not self._is_tool_route(route):
                    original_routes.append(route)
            
            # Replace routes
            self.app.router.routes = original_routes
            
            # Re-discover routers
            all_routers = discover_routers()
            self.all_routers.clear()
            
            # Re-register enabled routers
            for router in all_routers:
                tool_id = self._get_tool_id_from_router(router)
                if tool_id:
                    self.all_routers[tool_id] = router
                    
                    if tool_id in self.enabled_tools:
                        self.app.include_router(router)
                        logger.debug(f"Re-registered router for tool: {tool_id}")
            
            logger.info("App routes rebuilt successfully")
            
        except Exception as e:
            logger.error(f"Error rebuilding app routes: {e}")
    
    def _find_router_by_tool_id(self, tool_id: str) -> Optional[APIRouter]:
        """Find a router by tool ID."""
        if tool_id in self.all_routers:
            return self.all_routers[tool_id]
        
        # If not cached, try to discover
        all_routers = discover_routers()
        for router in all_routers:
            router_tool_id = self._get_tool_id_from_router(router)
            if router_tool_id == tool_id:
                self.all_routers[tool_id] = router
                return router
        
        return None
    
    def _get_tool_id_from_router(self, router: APIRouter) -> Optional[str]:
        """Get tool ID from a router using the same logic as RouteInspector."""
        try:
            return self.route_inspector._get_tool_id(router)
        except Exception as e:
            logger.warning(f"Error getting tool ID from router: {e}")
            return None
    
    def _is_tool_route(self, route) -> bool:
        """Check if a route belongs to a tool router."""
        # This is a simple heuristic - you might need to adjust based on your needs
        if hasattr(route, 'tags') and route.tags:
            # Routes with tags are likely tool routes
            return True
        if hasattr(route, 'path') and route.path.startswith(('/calc', '/time', '/web', '/think', '/fetch')):
            # Routes with known tool prefixes
            return True
        return False