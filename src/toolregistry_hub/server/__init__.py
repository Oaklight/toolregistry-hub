"""ToolRegistry Hub Server module.

This module provides FastAPI and MCP server implementations for ToolRegistry Hub tools.
It automatically exposes all available tools as REST API endpoints and MCP tools.

This module re-exports components from toolregistry-server for backward compatibility.
The actual server implementations have been migrated to the toolregistry-server package.

Example:
    ```python
    from toolregistry_hub.server import RouteTable, create_openapi_app
    from toolregistry_hub.server.registry import get_registry

    registry = get_registry()
    route_table = RouteTable(registry)
    app = create_openapi_app(route_table)
    ```

For new code, consider importing directly from toolregistry_server:
    ```python
    from toolregistry_server import RouteTable
    from toolregistry_server.openapi import create_openapi_app
    from toolregistry_server.mcp import create_mcp_server
    ```
"""

from typing import TYPE_CHECKING

# Re-export core components from toolregistry-server
try:
    from toolregistry_server import RouteEntry, RouteTable

    _SERVER_AVAILABLE = True
except ImportError:
    _SERVER_AVAILABLE = False
    RouteTable = None
    RouteEntry = None

# Lazy imports for protocol-specific components
if TYPE_CHECKING:
    from toolregistry_server.auth import (
        BearerTokenAuth,
        create_bearer_dependency,
        verify_token,
    )
    from toolregistry_server.mcp import (
        create_mcp_server,
        route_table_to_mcp_server,
        run_sse,
        run_stdio,
        run_streamable_http,
    )
    from toolregistry_server.openapi import create_openapi_app


def __getattr__(name: str):
    """Lazy import for backward compatibility.

    This allows importing components that require optional dependencies
    without failing at import time.
    """
    # OpenAPI components
    if name == "create_openapi_app":
        try:
            from toolregistry_server.openapi import create_openapi_app

            return create_openapi_app
        except ImportError as e:
            raise ImportError(
                "OpenAPI support requires toolregistry-server[openapi]. "
                "Install with: pip install toolregistry-hub[server_openapi]"
            ) from e

    # MCP components
    if name in (
        "create_mcp_server",
        "route_table_to_mcp_server",
        "run_stdio",
        "run_sse",
        "run_streamable_http",
    ):
        try:
            from toolregistry_server import mcp

            return getattr(mcp, name)
        except ImportError as e:
            raise ImportError(
                "MCP support requires toolregistry-server[mcp]. "
                "Install with: pip install toolregistry-hub[server_mcp]"
            ) from e

    # Auth components
    if name in ("BearerTokenAuth", "create_bearer_dependency", "verify_token"):
        try:
            from toolregistry_server import auth

            return getattr(auth, name)
        except ImportError as e:
            raise ImportError(
                "Auth support requires toolregistry-server[openapi]. "
                "Install with: pip install toolregistry-hub[server_openapi]"
            ) from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Core components
    "RouteTable",
    "RouteEntry",
    # OpenAPI components
    "create_openapi_app",
    # MCP components
    "create_mcp_server",
    "route_table_to_mcp_server",
    "run_stdio",
    "run_sse",
    "run_streamable_http",
    # Auth components
    "BearerTokenAuth",
    "create_bearer_dependency",
    "verify_token",
]
