"""Tests for declared output schemas on hub tools (#189)."""

from __future__ import annotations

import json

import pytest
from toolregistry_server import RouteTable

from toolregistry_hub.bash_tool import BashTool
from toolregistry_hub.datetime_utils import DateTime
from toolregistry_hub.file_ops import FileOps
from toolregistry_hub.path_info import PathInfo
from toolregistry_hub.server.output_schemas import OUTPUT_SCHEMAS
from toolregistry_hub.server.registry import build_registry


@pytest.fixture(scope="module")
def registry():
    """The hub registry, built once: metadata overrides are the subject."""
    return build_registry()


@pytest.fixture(scope="module")
def route_table(registry):
    return RouteTable(registry)


def _declared_tools():
    for namespace, methods in OUTPUT_SCHEMAS.items():
        for method, schema in methods.items():
            yield namespace, method, schema


def test_every_declared_schema_names_a_registered_tool(registry):
    """A renamed or moved method must fail here, not silently lose its schema."""
    registered = {
        (tool.namespace, tool.method_name) for tool in registry._tools.values()
    }
    declared = {(namespace, method) for namespace, method, _ in _declared_tools()}
    assert declared <= registered
    assert declared


def test_schemas_are_object_typed_with_typed_properties():
    """``structuredContent`` is an object, so every schema must describe one."""
    for namespace, method, schema in _declared_tools():
        where = f"{namespace}.{method}"
        assert schema["type"] == "object", where
        assert schema.get("additionalProperties") is True, where
        assert schema["properties"], where
        for field, spec in schema["properties"].items():
            assert "type" in spec, f"{where}.{field}"


def test_route_table_publishes_the_declared_schema(route_table, registry):
    """toolregistry-server reads metadata.extra, so the route must carry it."""
    for namespace, method, schema in _declared_tools():
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
        "fs/file_search-glob",
        "fs/file_search-grep",
        "web/websearch-search",
        "academics-search",
    ):
        route = route_table.get_route(name)
        assert route is not None, name
        assert route.output_schema is None, name


def _assert_matches(result, schema):
    """Every key the tool actually returned is declared in the schema."""
    unknown = set(result) - set(schema["properties"])
    assert not unknown


def test_path_info_result_matches_schema(tmp_path):
    path = tmp_path / "probe.txt"
    path.write_text("hello")
    _assert_matches(PathInfo.info(str(path)), OUTPUT_SCHEMAS["fs/path_info"]["info"])


def test_path_info_missing_result_matches_schema(tmp_path):
    """The missing-path shape is a subset, which is why nothing is required."""
    result = PathInfo.info(str(tmp_path / "nope.txt"))
    assert result == {"exists": False}
    _assert_matches(result, OUTPUT_SCHEMAS["fs/path_info"]["info"])


def test_file_ops_results_match_schemas(tmp_path):
    path = tmp_path / "notes.txt"
    written = FileOps.write(str(path), "hello\n")
    _assert_matches(written, OUTPUT_SCHEMAS["file_ops"]["write"])

    read = FileOps.read(str(path))
    _assert_matches(read, OUTPUT_SCHEMAS["file_ops"]["read"])

    edited = FileOps.edit(
        str(path),
        old_string="hello",
        new_string="world",
        digest=read["digest"],
    )
    _assert_matches(edited, OUTPUT_SCHEMAS["file_ops"]["edit"])


def test_read_digest_only_result_matches_schema(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello\n")
    _assert_matches(
        FileOps.read(str(path), digest_only=True),
        OUTPUT_SCHEMAS["file_ops"]["read"],
    )


def test_convert_timezone_result_matches_schema():
    _assert_matches(
        DateTime.convert_timezone("12:00", "UTC", "Asia/Shanghai"),
        OUTPUT_SCHEMAS["datetime"]["convert_timezone"],
    )


def test_bash_execute_result_matches_schema():
    _assert_matches(BashTool.execute("echo hi"), OUTPUT_SCHEMAS["bash"]["execute"])


def test_schema_is_published_with_no_required_list():
    """No field is required, so a tool may omit one without contradicting it."""
    for namespace, method, schema in _declared_tools():
        assert "required" not in schema, f"{namespace}.{method}"


def test_schemas_survive_json_round_trip():
    """The schemas cross process boundaries as JSON on both transports."""
    for namespace, method, schema in _declared_tools():
        assert json.loads(json.dumps(schema)) == schema, f"{namespace}.{method}"
