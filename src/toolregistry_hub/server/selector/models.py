"""Data models for the tool selector."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


class ToolEndpoint(BaseModel):
    """Tool endpoint information."""
    
    path: str
    methods: List[str]
    name: str = ""
    summary: str = ""
    operation_id: str = ""


class ToolConfig(BaseModel):
    """Tool configuration model."""
    
    id: str
    name: str
    prefix: str
    enabled: bool = True
    description: str = ""
    tags: List[str] = []
    endpoints: List[ToolEndpoint] = []
    module_name: str = ""


class ToolRegistry(BaseModel):
    """Tool registry containing all tool configurations."""
    
    tools: Dict[str, ToolConfig] = {}
    last_updated: datetime = datetime.now()
    version: str = "1.0.0"


class ToggleResponse(BaseModel):
    """Response for tool toggle operations."""
    
    success: bool
    message: str
    tool_id: str
    enabled: bool


class ServerStatusResponse(BaseModel):
    """Response for server status."""
    
    online: bool
    tools_count: int
    enabled_count: int
    last_reload: Optional[datetime] = None


class ReloadResponse(BaseModel):
    """Response for server reload operations."""
    
    success: bool
    message: str
    tools_discovered: int
    errors: List[str] = []