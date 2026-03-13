"""MCP adapter that creates an MCP low-level Server from a ToolRegistry.

This module bridges ToolRegistry and the MCP Python SDK's low-level Server API,
ensuring tool enable/disable state is always read directly from the registry
at request time (no drift).
"""

import json

from loguru import logger
from mcp.server.lowlevel import Server
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData, TextContent, Tool as MCPTool
from toolregistry import ToolRegistry


def registry_to_mcp_server(registry: ToolRegistry) -> Server:
    """Create an MCP low-level Server from a ToolRegistry.

    Registers list_tools and call_tool handlers that read directly
    from the registry, ensuring enable/disable state is always
    in sync (no drift).

    Args:
        registry: The ToolRegistry instance to expose as MCP tools.

    Returns:
        A configured mcp.server.lowlevel.Server instance.
    """
    server = Server("ToolRegistry-Hub")

    @server.list_tools()
    async def handle_list_tools() -> list[MCPTool]:
        """Return MCP tool definitions for all enabled tools in the registry."""
        tools: list[MCPTool] = []
        for tool_name in registry.list_tools():
            tool = registry.get_tool(tool_name)
            if tool is None:
                continue
            tools.append(
                MCPTool(
                    name=tool.name,
                    description=tool.description or "",
                    inputSchema=tool.parameters,
                )
            )
        logger.debug(f"list_tools: returning {len(tools)} enabled tools")
        return tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool by name with the given arguments.

        Args:
            name: The tool name to invoke.
            arguments: The input arguments for the tool.

        Returns:
            A list containing a single TextContent with the result.

        Raises:
            McpError: If the tool is disabled or not found.
        """
        # Check if tool is disabled
        if not registry.is_enabled(name):
            reason = registry.get_disable_reason(name) or "unknown reason"
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Tool '{name}' is disabled: {reason}",
                )
            )

        tool = registry.get_tool(name)
        if tool is None:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Tool '{name}' not found",
                )
            )

        try:
            if tool.is_async:
                result = await tool.arun(arguments)
            else:
                result = tool.run(arguments)

            # Serialize result to text
            if isinstance(result, (dict, list)):
                text = json.dumps(result, ensure_ascii=False, default=str)
            else:
                text = str(result)

            logger.debug(f"call_tool '{name}': success")
            return [TextContent(type="text", text=text)]

        except McpError:
            raise
        except Exception as e:
            logger.warning(f"call_tool '{name}': error - {e}")
            # Return error as content; the SDK's handler wrapper will catch
            # exceptions and set isError=True via _make_error_result.
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=str(e),
                )
            )

    return server
