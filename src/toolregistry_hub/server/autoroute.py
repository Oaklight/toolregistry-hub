"""Automatic route generation from a ToolRegistry.

Converts a :class:`~toolregistry.ToolRegistry` into a FastAPI
:class:`~fastapi.APIRouter` by introspecting each registered
:class:`~toolregistry.tool.Tool` and dynamically creating Pydantic
request models and route handlers.
"""

from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from loguru import logger
from pydantic import BaseModel, Field, create_model
from toolregistry import ToolRegistry
from toolregistry.tool import Tool

# ---------------------------------------------------------------------------
# JSON Schema type → Python type mapping
# ---------------------------------------------------------------------------

_JSON_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


# ---------------------------------------------------------------------------
# Helper: resolve a single field schema to a Python type
# ---------------------------------------------------------------------------


def _resolve_type(field_schema: dict[str, Any]) -> type:
    """Resolve a JSON Schema field description to a Python type.

    Handles basic types, ``array`` with ``items``, nested ``object`` with
    ``properties`` (recursively creates a Pydantic model), ``enum`` via
    ``Literal``, and falls back to ``Any`` for unknown schemas.

    Args:
        field_schema: A single-field JSON Schema dict (e.g.
            ``{"type": "string"}`` or ``{"type": "array", "items": {...}}``).

    Returns:
        The resolved Python type suitable for use in a Pydantic model field.
    """
    # Handle enum → Literal
    if "enum" in field_schema:
        from typing import Literal  # noqa: UP035 – needed at runtime

        values = tuple(field_schema["enum"])
        return Literal[values]  # ty: ignore[invalid-type-form]

    json_type = field_schema.get("type")

    if json_type == "array":
        items_schema = field_schema.get("items")
        if items_schema:
            inner = _resolve_type(items_schema)
            return list[inner]  # ty: ignore[invalid-type-form]
        return list

    if json_type == "object" and "properties" in field_schema:
        # Recursively build a nested Pydantic model
        return _schema_to_pydantic("NestedModel", field_schema)

    if json_type is not None:
        return _JSON_TYPE_MAP.get(json_type, Any)

    # anyOf / oneOf patterns (e.g. Optional fields from toolregistry)
    any_of = field_schema.get("anyOf") or field_schema.get("oneOf")
    if any_of:
        non_null = [s for s in any_of if s.get("type") != "null"]
        if len(non_null) == 1:
            return _resolve_type(non_null[0])

    return Any


# ---------------------------------------------------------------------------
# JSON Schema → Pydantic model
# ---------------------------------------------------------------------------


def _schema_to_pydantic(name: str, schema: dict[str, Any]) -> type[BaseModel]:
    """Convert a JSON Schema ``object`` definition into a dynamic Pydantic model.

    Args:
        name: The class name for the generated model.
        schema: A JSON Schema dict with ``properties`` (and optionally
            ``required``).

    Returns:
        A dynamically created :class:`pydantic.BaseModel` subclass whose
        fields mirror the schema properties.
    """
    properties: dict[str, Any] = schema.get("properties", {})
    if not properties:
        # Return an empty model when there are no properties
        return create_model(name)

    required_fields: list[str] = schema.get("required", [])
    field_definitions: dict[str, tuple[type, Any]] = {}

    for field_name, field_schema in properties.items():
        py_type = _resolve_type(field_schema)
        description = field_schema.get("description")

        is_required = field_name in required_fields
        default_value = field_schema.get("default", ... if is_required else None)

        field_kwargs: dict[str, Any] = {}
        if description:
            field_kwargs["description"] = description

        if default_value is ...:
            field_definitions[field_name] = (py_type, Field(**field_kwargs))
        else:
            field_definitions[field_name] = (
                py_type,
                Field(default=default_value, **field_kwargs),
            )

    return create_model(name, **field_definitions)  # ty: ignore[no-matching-overload]


# ---------------------------------------------------------------------------
# Route generation
# ---------------------------------------------------------------------------


def _add_route(router: APIRouter, tool: Tool, registry: ToolRegistry) -> None:
    """Create and register a POST route for a single tool.

    The route path is ``/{namespace}/{method_name}``.  If either attribute is
    ``None``, the values are inferred from ``tool.name`` by splitting on
    ``-``.

    For async tools the handler is an ``async def``; for sync tools a plain
    ``def`` is used.  A closure is used to correctly capture the loop
    variable.

    Each endpoint checks at request time whether the tool is still enabled
    via ``registry.is_enabled()``.  If the tool has been disabled at runtime,
    the endpoint returns HTTP 503 Service Unavailable.

    Args:
        router: The :class:`~fastapi.APIRouter` to add the route to.
        tool: The :class:`~toolregistry.tool.Tool` to expose.
        registry: The :class:`~toolregistry.ToolRegistry` used for runtime
            enable/disable checks.
    """
    namespace = tool.namespace
    method_name = tool.method_name

    # Infer namespace / method_name from tool.name when not set
    if namespace is None or method_name is None:
        parts = tool.name.split("-", 1)
        if len(parts) == 2:
            namespace = namespace or parts[0]
            method_name = method_name or parts[1]
        else:
            namespace = namespace or "default"
            method_name = method_name or tool.name

    path = f"/{namespace}/{method_name}"

    # Determine request model
    request_model: type[BaseModel]
    if tool.parameters_model is not None:
        request_model = tool.parameters_model
    else:
        model_name = f"{tool.name.replace('-', '_').title().replace('_', '')}Request"
        request_model = _schema_to_pydantic(model_name, tool.parameters)

    summary = (tool.description or "")[:120]
    # Use the top-level segment of the namespace as the tag for grouping
    # e.g. "web/brave_search" → tag "web", "calculator" → tag "calculator"
    if namespace:
        tag = namespace.split("/")[0]
        tags = [tag]
    else:
        tags = []

    # Capture tool_name as a string to avoid closure-over-loop-variable issues.
    tool_name = tool.name

    # Use factory functions to capture tool, RequestModel, registry, and
    # tool_name per iteration via closure.  We must NOT expose the Tool as a
    # default parameter because Pydantic v2 rejects underscore-prefixed field
    # names and FastAPI would try to treat it as a body parameter.

    if tool.is_async:

        def _make_async_endpoint(
            t: Tool = tool,
            M: type[BaseModel] = request_model,
            reg: ToolRegistry = registry,
            tname: str = tool_name,
        ):
            async def _endpoint(data: M) -> Any:  # ty: ignore[invalid-type-form]
                if not reg.is_enabled(tname):
                    raise HTTPException(
                        status_code=503,
                        detail=f"Tool '{tname}' is currently disabled",
                    )
                return await t.arun(data.model_dump())

            return _endpoint

        router.add_api_route(
            path,
            _make_async_endpoint(),
            methods=["POST"],
            operation_id=tool.name,
            summary=summary,
            tags=tags,  # ty: ignore[invalid-argument-type]
        )
    else:

        def _make_sync_endpoint(
            t: Tool = tool,
            M: type[BaseModel] = request_model,
            reg: ToolRegistry = registry,
            tname: str = tool_name,
        ):
            def _endpoint(data: M) -> Any:  # ty: ignore[invalid-type-form]
                if not reg.is_enabled(tname):
                    raise HTTPException(
                        status_code=503,
                        detail=f"Tool '{tname}' is currently disabled",
                    )
                return t.run(data.model_dump())

            return _endpoint

        router.add_api_route(
            path,
            _make_sync_endpoint(),
            methods=["POST"],
            operation_id=tool.name,
            summary=summary,
            tags=tags,  # ty: ignore[invalid-argument-type]
        )

    logger.debug(f"Auto-route registered: POST {router.prefix}{path} → {tool.name}")


def registry_to_router(
    registry: ToolRegistry,
    prefix: str = "/tools",
) -> APIRouter:
    """Convert a :class:`~toolregistry.ToolRegistry` into a FastAPI router.

    Routes are generated for **all** registered tools regardless of their
    current enabled/disabled state.  Each endpoint checks
    ``registry.is_enabled()`` at request time and returns HTTP 503 if the
    tool has been disabled, allowing runtime enable/disable without
    restarting the server.

    Args:
        registry: The tool registry to convert.
        prefix: URL prefix for all generated routes.

    Returns:
        A :class:`~fastapi.APIRouter` with one POST route per registered tool.
    """
    router = APIRouter(prefix=prefix)

    for tool in registry._tools.values():
        _add_route(router, tool, registry)

    logger.info(
        f"Auto-router created with {len(router.routes)} route(s) under '{prefix}'"
    )
    return router


# ---------------------------------------------------------------------------
# Dynamic OpenAPI schema generation
# ---------------------------------------------------------------------------


def setup_dynamic_openapi(app: FastAPI, registry: ToolRegistry) -> None:
    """Configure dynamic OpenAPI schema generation that filters out disabled tools.

    This replaces FastAPI's default cached OpenAPI schema with a dynamic one
    that checks tool enable/disable status on every request to ``/openapi.json``.
    Disabled tools are excluded from the schema so they do not appear in
    ``/docs`` or ``/openapi.json``, and re-enabling them makes them visible
    again immediately.

    Args:
        app: The FastAPI application instance.
        registry: The tool registry used for enable/disable status checks.
    """

    def custom_openapi() -> dict[str, Any]:
        # Generate a fresh OpenAPI schema on every call (no caching)
        # so it always reflects the current enable/disable state.
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Collect operation_ids of disabled tools
        disabled_operation_ids: set[str] = set()
        for tool in registry._tools.values():
            if not registry.is_enabled(tool.name):
                disabled_operation_ids.add(tool.name)

        # Filter out paths whose operations correspond to disabled tools
        if disabled_operation_ids and "paths" in openapi_schema:
            filtered_paths: dict[str, Any] = {}
            for path, path_item in openapi_schema["paths"].items():
                filtered_methods: dict[str, Any] = {}
                for method, operation in path_item.items():
                    if isinstance(operation, dict):
                        op_id = operation.get("operationId", "")
                        if op_id not in disabled_operation_ids:
                            filtered_methods[method] = operation
                    else:
                        filtered_methods[method] = operation
                if filtered_methods:
                    filtered_paths[path] = filtered_methods
            openapi_schema["paths"] = filtered_paths

        # Do NOT cache (app.openapi_schema is not set) so the schema
        # is regenerated on every request, reflecting runtime changes.
        return openapi_schema

    app.openapi = custom_openapi  # ty: ignore[invalid-assignment]
