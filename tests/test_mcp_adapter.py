"""Tests for the MCP adapter that bridges ToolRegistry to MCP Server.

Uses the MCP SDK's in-memory transport (create_connected_server_and_client_session)
for end-to-end testing of list_tools and call_tool handlers.
"""

import json

import pytest
from mcp.server.lowlevel import Server
from mcp.shared.memory import create_connected_server_and_client_session
from toolregistry import ToolRegistry

from toolregistry_hub.server.mcp_adapter import registry_to_mcp_server
from toolregistry_hub.server.server_mcp import create_mcp_server


# ---------------------------------------------------------------------------
# Test helper functions
# ---------------------------------------------------------------------------


def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        Sum of a and b.
    """
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two integers.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        Product of a and b.
    """
    return a * b


def greet(name: str) -> str:
    """Return a greeting string.

    Args:
        name: Name to greet.

    Returns:
        A greeting message.
    """
    return f"Hello, {name}!"


def get_info() -> dict:
    """Return a sample info dict.

    Returns:
        A dictionary with sample data.
    """
    return {"status": "ok", "count": 42}


def get_pi() -> float:
    """Return the value of pi.

    Returns:
        Pi approximation.
    """
    return 3.14159


def get_answer() -> int:
    """Return the answer to everything.

    Returns:
        The number 42.
    """
    return 42


def failing_tool() -> str:
    """A tool that always raises an exception.

    Returns:
        Never returns normally.

    Raises:
        ValueError: Always.
    """
    raise ValueError("intentional error for testing")


def crashing_tool(a: int, b: int) -> int:
    """A tool that raises a RuntimeError.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        Never returns normally.

    Raises:
        RuntimeError: Always.
    """
    raise RuntimeError("unexpected crash")


async def async_add(a: int, b: int) -> int:
    """Asynchronously add two integers.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        Sum of a and b.
    """
    return a + b


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry() -> ToolRegistry:
    """Create a ToolRegistry with add and multiply tools registered."""
    reg = ToolRegistry()
    reg.register(add)
    reg.register(multiply)
    return reg


# ---------------------------------------------------------------------------
# 1. registry_to_mcp_server() basic functionality
# ---------------------------------------------------------------------------


class TestRegistryToMcpServer:
    """Tests for registry_to_mcp_server() basic creation."""

    def test_returns_server_instance(self, registry: ToolRegistry) -> None:
        """Verify that registry_to_mcp_server returns an mcp Server instance."""
        server = registry_to_mcp_server(registry)
        assert isinstance(server, Server)

    def test_create_mcp_server_returns_server_instance(
        self, registry: ToolRegistry
    ) -> None:
        """Verify that create_mcp_server (server_mcp.py) also returns a Server."""
        server = create_mcp_server(registry)
        assert isinstance(server, Server)

    def test_server_has_correct_name(self, registry: ToolRegistry) -> None:
        """Verify the server name is set to 'ToolRegistry-Hub'."""
        server = registry_to_mcp_server(registry)
        assert server.name == "ToolRegistry-Hub"


# ---------------------------------------------------------------------------
# 2. list_tools handler
# ---------------------------------------------------------------------------


class TestListTools:
    """Tests for the list_tools MCP handler."""

    @pytest.mark.asyncio()
    async def test_list_tools_returns_registered_tools(
        self, registry: ToolRegistry
    ) -> None:
        """Verify list_tools returns all enabled tools from the registry."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.list_tools()
            tool_names = {t.name for t in result.tools}
            assert tool_names == {"add", "multiply"}

    @pytest.mark.asyncio()
    async def test_list_tools_name_and_description(
        self, registry: ToolRegistry
    ) -> None:
        """Verify tool name and description are correctly mapped."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.list_tools()
            tools_by_name = {t.name: t for t in result.tools}

            assert "add" in tools_by_name
            # Description may include the full docstring; check it starts correctly
            assert tools_by_name["add"].description.startswith("Add two integers.")

            assert "multiply" in tools_by_name
            assert tools_by_name["multiply"].description.startswith(
                "Multiply two integers."
            )

    @pytest.mark.asyncio()
    async def test_list_tools_input_schema(self, registry: ToolRegistry) -> None:
        """Verify inputSchema contains correct parameter definitions."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.list_tools()
            tools_by_name = {t.name: t for t in result.tools}

            schema = tools_by_name["add"].inputSchema
            assert schema["type"] == "object"
            assert "a" in schema["properties"]
            assert "b" in schema["properties"]
            assert schema["properties"]["a"]["type"] == "integer"
            assert schema["properties"]["b"]["type"] == "integer"
            assert set(schema["required"]) == {"a", "b"}


# ---------------------------------------------------------------------------
# 3. enable/disable dynamic reflection (key test)
# ---------------------------------------------------------------------------


class TestEnableDisable:
    """Tests for dynamic enable/disable reflection in list_tools."""

    @pytest.mark.asyncio()
    async def test_disable_removes_tool_from_list(self, registry: ToolRegistry) -> None:
        """Disabling a tool should remove it from list_tools results."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            # Initially both tools are listed
            result = await client.list_tools()
            assert {t.name for t in result.tools} == {"add", "multiply"}

            # Disable 'add'
            registry.disable("add")
            result = await client.list_tools()
            assert {t.name for t in result.tools} == {"multiply"}

    @pytest.mark.asyncio()
    async def test_enable_restores_tool_to_list(self, registry: ToolRegistry) -> None:
        """Re-enabling a tool should restore it in list_tools results."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            # Disable then re-enable
            registry.disable("add")
            result = await client.list_tools()
            assert {t.name for t in result.tools} == {"multiply"}

            registry.enable("add")
            result = await client.list_tools()
            assert {t.name for t in result.tools} == {"add", "multiply"}

    @pytest.mark.asyncio()
    async def test_full_enable_disable_cycle(self, registry: ToolRegistry) -> None:
        """Full cycle: list -> disable A -> list -> enable A -> list."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            # Step 1: Both tools present
            result = await client.list_tools()
            names = {t.name for t in result.tools}
            assert names == {"add", "multiply"}

            # Step 2: Disable 'add'
            registry.disable("add")
            result = await client.list_tools()
            names = {t.name for t in result.tools}
            assert names == {"multiply"}

            # Step 3: Re-enable 'add'
            registry.enable("add")
            result = await client.list_tools()
            names = {t.name for t in result.tools}
            assert names == {"add", "multiply"}


# ---------------------------------------------------------------------------
# 4. call_tool handler
# ---------------------------------------------------------------------------


class TestCallTool:
    """Tests for the call_tool MCP handler."""

    @pytest.mark.asyncio()
    async def test_call_enabled_tool(self, registry: ToolRegistry) -> None:
        """Calling an enabled tool should return the correct result."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("add", {"a": 3, "b": 4})
            assert result.isError is False
            assert len(result.content) == 1
            assert result.content[0].text == "7"

    @pytest.mark.asyncio()
    async def test_call_disabled_tool_returns_error(
        self, registry: ToolRegistry
    ) -> None:
        """Calling a disabled tool should return isError=True with reason."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            registry.disable("add", reason="maintenance")
            result = await client.call_tool("add", {"a": 1, "b": 2})
            assert result.isError is True
            assert "disabled" in result.content[0].text.lower()
            assert "maintenance" in result.content[0].text

    @pytest.mark.asyncio()
    async def test_call_nonexistent_tool_returns_error(
        self, registry: ToolRegistry
    ) -> None:
        """Calling a non-existent tool should return isError=True."""
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("nonexistent", {})
            assert result.isError is True
            assert "not found" in result.content[0].text.lower()


# ---------------------------------------------------------------------------
# 5. sync/async tool tests
# ---------------------------------------------------------------------------


class TestSyncAsyncTools:
    """Tests for both synchronous and asynchronous tool execution."""

    @pytest.mark.asyncio()
    async def test_sync_tool_execution(self) -> None:
        """A synchronous tool should execute correctly via call_tool."""
        registry = ToolRegistry()
        registry.register(add)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("add", {"a": 10, "b": 20})
            assert result.isError is False
            assert result.content[0].text == "30"

    @pytest.mark.asyncio()
    async def test_async_tool_execution(self) -> None:
        """An asynchronous tool should execute correctly via call_tool."""
        registry = ToolRegistry()
        registry.register(async_add)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("async_add", {"a": 5, "b": 7})
            assert result.isError is False
            assert result.content[0].text == "12"

    @pytest.mark.asyncio()
    async def test_mixed_sync_async_tools(self) -> None:
        """Both sync and async tools should coexist and work correctly."""
        registry = ToolRegistry()
        registry.register(add)
        registry.register(async_add)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            # Verify both are listed
            tools_result = await client.list_tools()
            tool_names = {t.name for t in tools_result.tools}
            assert tool_names == {"add", "async_add"}

            # Call sync tool
            r1 = await client.call_tool("add", {"a": 1, "b": 2})
            assert r1.content[0].text == "3"

            # Call async tool
            r2 = await client.call_tool("async_add", {"a": 3, "b": 4})
            assert r2.content[0].text == "7"


# ---------------------------------------------------------------------------
# 6. Result serialization tests
# ---------------------------------------------------------------------------


class TestResultSerialization:
    """Tests for result serialization in call_tool responses."""

    @pytest.mark.asyncio()
    async def test_dict_result_json_serialized(self) -> None:
        """A dict result should be JSON-serialized."""
        registry = ToolRegistry()
        registry.register(get_info)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("get_info", {})
            assert result.isError is False
            parsed = json.loads(result.content[0].text)
            assert parsed == {"status": "ok", "count": 42}

    @pytest.mark.asyncio()
    async def test_str_result_direct_string(self) -> None:
        """A str result should be returned as-is."""
        registry = ToolRegistry()
        registry.register(greet)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("greet", {"name": "World"})
            assert result.isError is False
            assert result.content[0].text == "Hello, World!"

    @pytest.mark.asyncio()
    async def test_int_result_str_conversion(self) -> None:
        """An int result should be converted via str()."""
        registry = ToolRegistry()
        registry.register(get_answer)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("get_answer", {})
            assert result.isError is False
            assert result.content[0].text == "42"

    @pytest.mark.asyncio()
    async def test_float_result_str_conversion(self) -> None:
        """A float result should be converted via str()."""
        registry = ToolRegistry()
        registry.register(get_pi)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("get_pi", {})
            assert result.isError is False
            assert result.content[0].text == "3.14159"

    @pytest.mark.asyncio()
    async def test_list_result_json_serialized(self) -> None:
        """A list result should be JSON-serialized."""

        def get_items() -> list:
            """Return a sample list.

            Returns:
                A list of items.
            """
            return [1, "two", 3.0]

        registry = ToolRegistry()
        registry.register(get_items)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("get_items", {})
            assert result.isError is False
            parsed = json.loads(result.content[0].text)
            assert parsed == [1, "two", 3.0]


# ---------------------------------------------------------------------------
# 7. Exception handling tests
# ---------------------------------------------------------------------------


class TestExceptionHandling:
    """Tests for exception handling in call_tool."""

    @pytest.mark.asyncio()
    async def test_tool_execution_error_returns_error_message(self) -> None:
        """When a tool raises an exception, ToolRegistry catches it and returns
        an error string. The adapter should return this as normal content.
        """
        registry = ToolRegistry()
        registry.register(failing_tool)
        server = registry_to_mcp_server(registry)
        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("failing_tool", {})
            # ToolRegistry.run() catches the exception internally and returns
            # an error string, so isError is False but text contains the error.
            assert result.isError is False
            assert "intentional error for testing" in result.content[0].text

    @pytest.mark.asyncio()
    async def test_exception_propagation_returns_error_text(self) -> None:
        """When a tool's callable raises, ToolRegistry catches it and returns
        an error string. The adapter serializes this as normal text content.
        """
        registry = ToolRegistry()
        registry.register(crashing_tool)
        server = registry_to_mcp_server(registry)

        async with create_connected_server_and_client_session(server) as client:
            result = await client.call_tool("crashing_tool", {"a": 1, "b": 2})
            # ToolRegistry.run() catches the exception and returns an error
            # string. The adapter treats this as a normal string result.
            assert "unexpected crash" in result.content[0].text
