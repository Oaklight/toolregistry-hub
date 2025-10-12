from fastmcp import FastMCP

from .server_openapi import app

mcp_app = FastMCP.from_fastapi(app, name="ToolRegistry-Hub MCP Server")
