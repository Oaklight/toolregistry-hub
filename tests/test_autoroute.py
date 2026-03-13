"""Tests for the automatic route generation module (autoroute.py).

Covers:
- _schema_to_pydantic: JSON Schema → Pydantic model conversion
- _resolve_type: single-field type resolution
- registry_to_router: ToolRegistry → APIRouter conversion
- _add_route: individual route registration (sync / async)
- Integration tests with create_core_app()
"""

import asyncio
from typing import Any, Literal, get_args, get_origin

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from toolregistry import ToolRegistry

from toolregistry_hub.server.autoroute import (
    _add_route,
    _resolve_type,
    _schema_to_pydantic,
    registry_to_router,
    setup_dynamic_openapi,
)


# =========================================================================
# 1a. _schema_to_pydantic tests
# =========================================================================


class TestSchemaToPydantic:
    """Tests for _schema_to_pydantic."""

    def test_empty_schema(self):
        """Empty schema {} should return an empty Pydantic model."""
        Model = _schema_to_pydantic("EmptyModel", {})
        assert issubclass(Model, BaseModel)
        # Should have no user-defined fields
        assert len(Model.model_fields) == 0
        # Should be instantiable with no arguments
        instance = Model()
        assert instance is not None

    def test_basic_types(self):
        """Test string, integer, number, boolean type mapping."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "score": {"type": "number"},
                "active": {"type": "boolean"},
            },
            "required": ["name", "age", "score", "active"],
        }
        Model = _schema_to_pydantic("BasicModel", schema)
        fields = Model.model_fields

        assert fields["name"].annotation is str
        assert fields["age"].annotation is int
        assert fields["score"].annotation is float
        assert fields["active"].annotation is bool

    def test_required_and_optional(self):
        """Required fields have no default; optional fields default to None."""
        schema = {
            "type": "object",
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["required_field"],
        }
        Model = _schema_to_pydantic("ReqOptModel", schema)
        fields = Model.model_fields

        # Required field should not have a default (is_required)
        assert fields["required_field"].is_required()
        # Optional field should have default None
        assert not fields["optional_field"].is_required()
        assert fields["optional_field"].default is None

    def test_default_values(self):
        """Schema-specified default values should be preserved."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 10},
                "label": {"type": "string", "default": "hello"},
            },
            "required": [],
        }
        Model = _schema_to_pydantic("DefaultModel", schema)
        fields = Model.model_fields

        assert fields["count"].default == 10
        assert fields["label"].default == "hello"

        # Instantiate with defaults
        instance = Model()
        assert instance.count == 10  # ty: ignore[unresolved-attribute]
        assert instance.label == "hello"  # ty: ignore[unresolved-attribute]

    def test_array_type(self):
        """Array with items should map to List[inner_type]."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["tags"],
        }
        Model = _schema_to_pydantic("ArrayModel", schema)
        field_type = Model.model_fields["tags"].annotation

        assert get_origin(field_type) is list
        args = get_args(field_type)
        assert len(args) == 1
        assert args[0] is str

    def test_nested_object(self):
        """Nested object should recursively create a nested Pydantic model."""
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                    "required": ["street"],
                },
            },
            "required": ["address"],
        }
        Model = _schema_to_pydantic("NestedModel", schema)
        address_type = Model.model_fields["address"].annotation

        # Should be a Pydantic model subclass
        assert issubclass(address_type, BaseModel)
        nested_fields = address_type.model_fields
        assert "street" in nested_fields
        assert "city" in nested_fields

    def test_enum_type(self):
        """Fields with enum should use Literal type."""
        schema = {
            "type": "object",
            "properties": {
                "color": {"type": "string", "enum": ["red", "green", "blue"]},
            },
            "required": ["color"],
        }
        Model = _schema_to_pydantic("EnumModel", schema)
        field_type = Model.model_fields["color"].annotation

        assert get_origin(field_type) is Literal
        assert set(get_args(field_type)) == {"red", "green", "blue"}


# =========================================================================
# 1b. _resolve_type tests
# =========================================================================


class TestResolveType:
    """Tests for _resolve_type."""

    def test_basic_type_mapping(self):
        """Verify all basic JSON Schema types map correctly."""
        assert _resolve_type({"type": "string"}) is str
        assert _resolve_type({"type": "integer"}) is int
        assert _resolve_type({"type": "number"}) is float
        assert _resolve_type({"type": "boolean"}) is bool
        assert _resolve_type({"type": "array"}) is list
        assert _resolve_type({"type": "object"}) is dict

    def test_unknown_type_fallback(self):
        """Unknown type should fallback to Any."""
        result = _resolve_type({"type": "foobar"})
        assert result is Any

    def test_no_type_fallback(self):
        """Schema without type key should fallback to Any."""
        result = _resolve_type({})
        assert result is Any


# =========================================================================
# 1c. registry_to_router tests
# =========================================================================


def _make_simple_registry() -> ToolRegistry:
    """Create a simple ToolRegistry with one function for testing."""
    registry = ToolRegistry()

    def greet(name: str) -> str:
        """Say hello."""
        return f"Hello, {name}!"

    registry.register(greet, namespace="test")
    return registry


class TestRegistryToRouter:
    """Tests for registry_to_router."""

    def test_router_generation(self):
        """A simple registry should produce a router with routes."""
        registry = _make_simple_registry()
        router = registry_to_router(registry, prefix="/tools")

        assert isinstance(router, APIRouter)
        # Should have at least one route
        assert len(router.routes) > 0

    def test_disabled_tools_return_503(self):
        """Disabled tools should have routes but return 503 when called."""
        registry = _make_simple_registry()
        # Find the tool name and disable it
        tool_names = list(registry._tools.keys())
        assert len(tool_names) > 0
        for name in tool_names:
            registry.disable(name)

        router = registry_to_router(registry, prefix="/tools")
        # Routes should still be generated for disabled tools
        assert len(router.routes) > 0

        # Calling a disabled tool should return 503
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post("/tools/test/greet", json={"name": "World"})
        assert response.status_code == 503
        assert "currently disabled" in response.json()["detail"]

    def test_runtime_disable(self):
        """Disabling a tool at runtime should cause its endpoint to return 503."""
        registry = _make_simple_registry()
        router = registry_to_router(registry, prefix="/tools")

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Tool is enabled — should work
        response = client.post("/tools/test/greet", json={"name": "World"})
        assert response.status_code == 200

        # Disable at runtime
        tool_name = list(registry._tools.keys())[0]
        registry.disable(tool_name)

        # Now should return 503
        response = client.post("/tools/test/greet", json={"name": "World"})
        assert response.status_code == 503
        assert "currently disabled" in response.json()["detail"]

    def test_runtime_enable(self):
        """Re-enabling a tool at runtime should restore its endpoint."""
        registry = _make_simple_registry()
        tool_name = list(registry._tools.keys())[0]
        registry.disable(tool_name)

        router = registry_to_router(registry, prefix="/tools")

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Tool is disabled — should return 503
        response = client.post("/tools/test/greet", json={"name": "World"})
        assert response.status_code == 503

        # Re-enable at runtime
        registry.enable(tool_name)

        # Now should work
        response = client.post("/tools/test/greet", json={"name": "World"})
        assert response.status_code == 200

    def test_route_path_format(self):
        """Route paths should follow /tools/{namespace}/{method_name} format."""
        registry = _make_simple_registry()
        router = registry_to_router(registry, prefix="/tools")

        paths = [route.path for route in router.routes]  # ty: ignore[unresolved-attribute]
        # The tool registered with namespace="test" and function name "greet"
        # should produce path /test/greet
        assert any("/test/greet" in p for p in paths)


# =========================================================================
# 1d. _add_route tests
# =========================================================================


class TestAddRoute:
    """Tests for _add_route."""

    def test_sync_endpoint(self):
        """Sync tool should generate a sync endpoint."""
        registry = ToolRegistry()

        def add(a: float, b: float) -> float:
            """Add two numbers."""
            return a + b

        registry.register(add, namespace="math")
        tool = list(registry._tools.values())[0]

        router = APIRouter()
        _add_route(router, tool, registry)

        assert len(router.routes) == 1
        route = router.routes[0]
        # The endpoint should NOT be a coroutine function for sync tools
        assert not asyncio.iscoroutinefunction(route.endpoint)  # ty: ignore[unresolved-attribute]

    def test_async_endpoint(self):
        """Async tool should generate an async endpoint."""
        registry = ToolRegistry()

        async def async_fetch(url: str) -> str:
            """Fetch a URL."""
            return f"fetched: {url}"

        registry.register(async_fetch, namespace="net")
        tool = list(registry._tools.values())[0]

        router = APIRouter()
        _add_route(router, tool, registry)

        assert len(router.routes) == 1
        route = router.routes[0]
        # The endpoint SHOULD be a coroutine function for async tools
        assert asyncio.iscoroutinefunction(route.endpoint)  # ty: ignore[unresolved-attribute]


# =========================================================================
# 1e. Integration tests
# =========================================================================


class TestIntegration:
    """Integration tests with create_core_app()."""

    @pytest.fixture(autouse=True)
    def _reset_registry_singleton(self):
        """Reset the registry singleton before and after each test."""
        from toolregistry_hub.server import registry as registry_module

        original = registry_module._registry
        registry_module._registry = None
        yield
        registry_module._registry = original

    def test_core_app_has_auto_routes(self):
        """create_core_app() should include /tools/ prefix routes."""
        from toolregistry_hub.server.server_core import create_core_app

        app = create_core_app()
        paths = [route.path for route in app.routes]  # ty: ignore[unresolved-attribute]
        tools_paths = [p for p in paths if p.startswith("/tools/")]
        assert len(tools_paths) > 0, f"Expected /tools/ routes, got paths: {paths}"

    def test_core_app_has_version_route(self):
        """create_core_app() should include the version metadata route."""
        from toolregistry_hub.server.server_core import create_core_app

        app = create_core_app()
        paths = [route.path for route in app.routes]  # ty: ignore[unresolved-attribute]
        has_version = any(p.startswith("/version") for p in paths)
        assert has_version, f"Expected /version routes, got paths: {paths}"

    def test_calculator_auto_route_works(self):
        """POST /tools/calculator/evaluate should return the correct result."""
        from toolregistry_hub.server.server_core import create_core_app

        app = create_core_app()
        client = TestClient(app)

        response = client.post(
            "/tools/calculator/evaluate",
            json={"expression": "2 + 3"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == 5 or data == 5.0


# =========================================================================
# 1f. Dynamic OpenAPI schema tests
# =========================================================================


def _make_two_tool_registry() -> ToolRegistry:
    """Create a ToolRegistry with two tools for OpenAPI filtering tests."""
    registry = ToolRegistry()

    def greet(name: str) -> str:
        """Say hello."""
        return f"Hello, {name}!"

    def farewell(name: str) -> str:
        """Say goodbye."""
        return f"Goodbye, {name}!"

    registry.register(greet, namespace="test")
    registry.register(farewell, namespace="test")
    return registry


class TestDynamicOpenAPI:
    """Tests for setup_dynamic_openapi."""

    def _make_app(self, registry: ToolRegistry) -> FastAPI:
        """Build a minimal FastAPI app with auto-routes and dynamic OpenAPI."""
        app = FastAPI(title="Test", version="0.0.1")
        router = registry_to_router(registry, prefix="/tools")
        app.include_router(router)
        setup_dynamic_openapi(app, registry)
        return app

    def test_openapi_schema_hides_disabled_tools(self):
        """Disabled tools should not appear in /openapi.json."""
        registry = _make_two_tool_registry()
        tool_names = list(registry._tools.keys())
        # Disable the first tool
        registry.disable(tool_names[0])

        app = self._make_app(registry)
        client = TestClient(app)

        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Collect all operationIds in the schema
        operation_ids = set()
        for path_item in schema.get("paths", {}).values():
            for method_detail in path_item.values():
                if isinstance(method_detail, dict) and "operationId" in method_detail:
                    operation_ids.add(method_detail["operationId"])

        assert tool_names[0] not in operation_ids, (
            f"Disabled tool '{tool_names[0]}' should not appear in OpenAPI schema"
        )
        assert tool_names[1] in operation_ids, (
            f"Enabled tool '{tool_names[1]}' should appear in OpenAPI schema"
        )

    def test_openapi_schema_shows_enabled_tools(self):
        """All enabled tools should appear in /openapi.json."""
        registry = _make_two_tool_registry()

        app = self._make_app(registry)
        client = TestClient(app)

        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        operation_ids = set()
        for path_item in schema.get("paths", {}).values():
            for method_detail in path_item.values():
                if isinstance(method_detail, dict) and "operationId" in method_detail:
                    operation_ids.add(method_detail["operationId"])

        for name in registry._tools:
            assert name in operation_ids, (
                f"Enabled tool '{name}' should appear in OpenAPI schema"
            )

    def test_openapi_schema_dynamic_update(self):
        """Disabling/enabling a tool at runtime should update the schema dynamically."""
        registry = _make_two_tool_registry()
        tool_names = list(registry._tools.keys())

        app = self._make_app(registry)
        client = TestClient(app)

        def _get_operation_ids() -> set:
            resp = client.get("/openapi.json")
            assert resp.status_code == 200
            schema = resp.json()
            ids = set()
            for path_item in schema.get("paths", {}).values():
                for method_detail in path_item.values():
                    if (
                        isinstance(method_detail, dict)
                        and "operationId" in method_detail
                    ):
                        ids.add(method_detail["operationId"])
            return ids

        # Initially both tools should be visible
        ids = _get_operation_ids()
        assert tool_names[0] in ids
        assert tool_names[1] in ids

        # Disable the first tool — it should disappear from the schema
        registry.disable(tool_names[0])
        ids = _get_operation_ids()
        assert tool_names[0] not in ids
        assert tool_names[1] in ids

        # Re-enable the first tool — it should reappear
        registry.enable(tool_names[0])
        ids = _get_operation_ids()
        assert tool_names[0] in ids
        assert tool_names[1] in ids

        # Disable both tools — paths should be empty or absent
        registry.disable(tool_names[0])
        registry.disable(tool_names[1])
        ids = _get_operation_ids()
        assert tool_names[0] not in ids
        assert tool_names[1] not in ids
