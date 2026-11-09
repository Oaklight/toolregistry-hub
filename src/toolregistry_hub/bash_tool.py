"""Shell command execution tool with built-in safety validation.

This module re-exports from the standalone ``bashtool`` package
(git submodule at ``bashtool/``).  All implementation lives there.

Usage::

    from toolregistry_hub import BashTool

    result = BashTool.execute("ls -la")
"""

from typing import TypedDict

from toolregistry import ToolTag

from ._metadata import tool_metadata
from .bashtool import BashTool
from .bashtool import validate_command as _validate_command


class BashResult(TypedDict, total=False):
    """Result of ``BashTool.execute``."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


# ``BashTool`` lives in the bashtool submodule, which Hub does not edit.  The
# declaration is attached to the function class registration re-uses, so the
# tool carries it exactly like a decorated Hub method.
#
# The method's return type is annotated the same way: the submodule declares
# a bare ``dict``, and the declared ``output_schema`` above is the contract.
# Writing the annotation on the shared function keeps the tool typed without
# wrapping or replacing it; nothing reads the annotation at runtime.
BashTool.execute.__annotations__["return"] = BashResult

tool_metadata(
    defer=True,
    tags={ToolTag.DESTRUCTIVE, ToolTag.PRIVILEGED},
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=False,
    open_world_hint=True,
    title="Execute Shell Command",
    extra={
        "output_schema": {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
                "timed_out": {"type": "boolean"},
            },
            "additionalProperties": True,
        }
    },
)(BashTool.execute)

__all__ = ["BashTool", "_validate_command"]
