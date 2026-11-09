"""Tests for declared output schemas on hub tools (#189).

A tool declares its result shape at definition time with
``@tool_metadata(extra={"output_schema": ...})``, next to the method.  The
registry is the source of truth here: there is no namespace table to drift
from the definition.
"""

from __future__ import annotations

import json
from typing import get_type_hints, is_typeddict

import pytest
from toolregistry_server import RouteTable

from toolregistry_hub.bash_tool import BashTool
from toolregistry_hub.datetime_utils import DateTime
from toolregistry_hub.file_ops import FileOps
from toolregistry_hub.path_info import PathInfo
from toolregistry_hub.server.registry import build_registry

#: (namespace, method) pairs that must carry a declaration.
EXPECTED = {
    ("weather", "get_current"),
    ("weather", "get_forecast"),
    ("weather", "get_astronomy"),
    ("datetime", "convert_timezone"),
    ("file_ops", "read"),
    ("file_ops", "edit"),
    ("file_ops", "write"),
    ("fs", "info"),
    ("web", "fetch_content"),
    ("bash", "execute"),
}


@pytest.fixture(scope="module")
def registry():
    """The hub registry, built once: metadata declarations are the subject."""
    return build_registry()


@pytest.fixture(scope="module")
def route_table(registry):
    return RouteTable(registry)


def _declared_tools(registry):
    for tool in registry._tools.values():
        schema = (tool.metadata.extra or {}).get("output_schema")
        if schema is not None:
            yield tool.namespace, tool.method_name, schema


def _schema(registry, namespace: str, method: str) -> dict:
    for tool in registry._tools.values():
        if tool.namespace == namespace and tool.method_name == method:
            return tool.metadata.extra["output_schema"]
    raise AssertionError(f"{namespace}.{method} is not registered")


def test_every_expected_schema_is_declared_and_registered(registry):
    """A renamed or moved method must fail here, not silently lose its schema."""
    registered = {
        (tool.namespace, tool.method_name) for tool in registry._tools.values()
    }
    declared = {
        (namespace, method) for namespace, method, _ in _declared_tools(registry)
    }
    assert declared == EXPECTED
    assert declared <= registered


def test_every_output_schema_tool_has_a_typed_return_annotation(registry):
    """A declared schema must be backed by a TypedDict return annotation.

    The annotation is documentation and tooling input; it does not feed the
    published ``outputSchema``.  It is what a new tool is easiest to forget,
    so it is asserted for every schema-carrying tool rather than spot-checked.
    """
    schema_tools = [
        tool
        for tool in registry._tools.values()
        if (tool.metadata.extra or {}).get("output_schema") is not None
    ]
    assert len(schema_tools) == len(EXPECTED)
    untyped = [
        f"{tool.namespace}.{tool.method_name}"
        for tool in schema_tools
        if not is_typeddict(get_type_hints(tool.fn).get("return"))
    ]
    assert untyped == []


def test_schemas_are_object_typed_with_typed_properties(registry):
    """``structuredContent`` is an object, so every schema must describe one."""
    for namespace, method, schema in _declared_tools(registry):
        where = f"{namespace}.{method}"
        assert schema["type"] == "object", where
        assert schema.get("additionalProperties") is True, where
        assert schema["properties"], where
        for field, spec in schema["properties"].items():
            assert "type" in spec, f"{where}.{field}"


def test_route_table_publishes_the_declared_schema(route_table, registry):
    """toolregistry-server reads metadata.extra, so the route must carry it."""
    for namespace, method, schema in _declared_tools(registry):
        name = next(
            tool.name
            for tool in registry._tools.values()
            if tool.namespace == namespace and tool.method_name == method
        )
        route = route_table.get_route(name)
        assert route is not None, name
        assert route.output_schema == schema, name


def test_array_returning_tools_declare_no_schema(route_table):
    """MCP structuredContent is an object; arrays are deliberately excluded."""
    for name in (
        "fs-glob",
        "fs-grep",
        "web-search",
        "academics-search",
    ):
        route = route_table.get_route(name)
        assert route is not None, name
        assert route.output_schema is None, name


def _assert_matches(result, schema):
    """Every key the tool actually returned is declared in the schema."""
    unknown = set(result) - set(schema["properties"])
    assert not unknown


def test_path_info_result_matches_schema(tmp_path, registry):
    path = tmp_path / "probe.txt"
    path.write_text("hello")
    _assert_matches(PathInfo.info(str(path)), _schema(registry, "fs", "info"))


def test_path_info_missing_result_matches_schema(tmp_path, registry):
    """The missing-path shape is a subset, which is why nothing is required."""
    result = PathInfo.info(str(tmp_path / "nope.txt"))
    assert result == {"exists": False}
    _assert_matches(result, _schema(registry, "fs", "info"))


def test_file_ops_results_match_schemas(tmp_path, registry):
    path = tmp_path / "notes.txt"
    written = FileOps.write(str(path), "hello\n")
    _assert_matches(written, _schema(registry, "file_ops", "write"))

    read = FileOps.read(str(path))
    _assert_matches(read, _schema(registry, "file_ops", "read"))

    edited = FileOps.edit(
        str(path),
        old_string="hello",
        new_string="world",
        digest=read["digest"],
    )
    _assert_matches(edited, _schema(registry, "file_ops", "edit"))


def test_read_digest_only_result_matches_schema(tmp_path, registry):
    path = tmp_path / "notes.txt"
    path.write_text("hello\n")
    _assert_matches(
        FileOps.read(str(path), digest_only=True),
        _schema(registry, "file_ops", "read"),
    )


def test_convert_timezone_result_matches_schema(registry):
    _assert_matches(
        DateTime.convert_timezone("12:00", "UTC", "Asia/Shanghai"),
        _schema(registry, "datetime", "convert_timezone"),
    )


def test_bash_execute_result_matches_schema(registry):
    _assert_matches(BashTool.execute("echo hi"), _schema(registry, "bash", "execute"))


def test_schema_is_published_with_no_required_list(registry):
    """No field is required, so a tool may omit one without contradicting it."""
    for namespace, method, schema in _declared_tools(registry):
        assert "required" not in schema, f"{namespace}.{method}"


def test_schemas_survive_json_round_trip(registry):
    """The schemas cross process boundaries as JSON on both transports."""
    for namespace, method, schema in _declared_tools(registry):
        assert json.loads(json.dumps(schema)) == schema, f"{namespace}.{method}"
