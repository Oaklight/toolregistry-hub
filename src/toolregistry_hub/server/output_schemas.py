"""JSON Schemas for the hub tools that return structured results.

A tool declares its result shape through ``ToolMetadata.extra["output_schema"]``;
``toolregistry-server`` reads it when building the route table and the MCP
adapter then publishes ``outputSchema`` in ``tools/list`` and returns
``structuredContent`` alongside the text block for dict/list results.

Only tools whose result is a **dict with stable keys** are declared here.
Array-returning tools (``fs-glob``, ``fs-grep``,
``web-search``) are intentionally left out: MCP's
``structuredContent`` is an object, so an array result has nothing to
populate it with.

The schemas describe the keys each tool *always* emits.  They deliberately
declare no ``required`` list and set ``additionalProperties: true`` so a tool
that omits a field (``fs-info`` returns only ``{"exists": false}``
for a missing path) or grows a new one never contradicts its published
schema.  Types are only given where the tool guarantees them; fields whose
type varies with the upstream API are left untyped.
"""

from __future__ import annotations

from typing import Any

#: Resolved place name returned inside the weather results.
_AREA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "region": {"type": "string"},
        "country": {"type": "string"},
        "latitude": {"type": "string"},
        "longitude": {"type": "string"},
    },
    "additionalProperties": True,
}

#: One hour inside a forecast day (only present with ``include_hourly``).
_HOURLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "time": {"type": "string"},
        "temperature": {"type": "string"},
        "feels_like": {"type": "string"},
        "description": {"type": "string"},
        "humidity": {"type": "string"},
        "wind": {"type": "string"},
        "precipitation": {"type": "string"},
        "chance_of_rain": {"type": "string"},
        "chance_of_snow": {"type": "string"},
    },
    "additionalProperties": True,
}

#: One day inside a forecast.
_DAY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "date": {"type": "string"},
        "max_temp": {"type": "string"},
        "min_temp": {"type": "string"},
        "avg_temp": {"type": "string"},
        "uv_index": {"type": ["string", "integer"]},
        "total_snow_cm": {"type": ["string", "number"]},
        "sun_hours": {"type": ["string", "number"]},
        "sunrise": {"type": "string"},
        "sunset": {"type": "string"},
        "moon_phase": {"type": "string"},
        "hourly": {"type": "array", "items": _HOURLY_SCHEMA},
    },
    "additionalProperties": True,
}

_CURRENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "temperature": {"type": "string"},
        "feels_like": {"type": "string"},
        "description": {"type": "string"},
        "humidity": {"type": "string"},
        "wind": {"type": "string"},
        "precipitation": {"type": "string"},
        "cloud_cover": {"type": "string"},
        "uv_index": {"type": ["string", "integer"]},
        "visibility": {"type": "string"},
        "pressure": {"type": "string"},
    },
    "additionalProperties": True,
}

#: namespace → method name → result schema.
OUTPUT_SCHEMAS: dict[str, dict[str, dict[str, Any]]] = {
    "weather": {
        "get_current": {
            "type": "object",
            "properties": {
                "location": _AREA_SCHEMA,
                "current": _CURRENT_SCHEMA,
            },
            "additionalProperties": True,
        },
        "get_forecast": {
            "type": "object",
            "properties": {
                "location": _AREA_SCHEMA,
                "forecast": {"type": "array", "items": _DAY_SCHEMA},
            },
            "additionalProperties": True,
        },
        "get_astronomy": {
            "type": "object",
            "properties": {
                "location": _AREA_SCHEMA,
                "date": {"type": "string"},
                "sunrise": {"type": "string"},
                "sunset": {"type": "string"},
                "moonrise": {"type": "string"},
                "moonset": {"type": "string"},
                "moon_phase": {"type": "string"},
                "moon_illumination": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    "datetime": {
        "convert_timezone": {
            "type": "object",
            "properties": {
                "source_time": {"type": "string"},
                "target_time": {"type": "string"},
                "time_difference": {"type": "string"},
                "source_timezone": {"type": "string"},
                "target_timezone": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    "file_ops": {
        "read": {
            "type": "object",
            "properties": {
                "digest": {"type": "string"},
                "is_symlink": {"type": "boolean"},
                "real_path": {"type": "string"},
                "content": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "edit": {
            "type": "object",
            "properties": {
                "diff": {"type": "string"},
                "digest": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "write": {
            "type": "object",
            "properties": {"digest": {"type": "string"}},
            "additionalProperties": True,
        },
    },
    "fs": {
        "info": {
            "type": "object",
            "properties": {
                "exists": {"type": "boolean"},
                "type": {"type": "string"},
                "size": {"type": "integer"},
                "last_modified": {"type": "string"},
                "permissions": {"type": "string"},
            },
            "additionalProperties": True,
        },
    },
    "web": {
        "fetch_content": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "url": {"type": "string"},
                "strategy": {"type": "string"},
                "quality": {"type": "string"},
                "content_type": {"type": "string"},
                "cached": {"type": "boolean"},
                "elapsed_ms": {"type": "integer"},
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "additionalProperties": True,
        },
    },
    "bash": {
        "execute": {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
                "timed_out": {"type": "boolean"},
            },
            "additionalProperties": True,
        },
    },
}
