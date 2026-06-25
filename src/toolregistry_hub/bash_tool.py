"""Shell command execution tool with built-in safety validation.

This module re-exports from the standalone ``bashtool`` package
(git submodule at ``bashtool/``).  All implementation lives there.

Usage::

    from toolregistry_hub import BashTool

    result = BashTool.execute("ls -la")
"""

from .bashtool import BashTool
from .bashtool.bashtool import validate_command as _validate_command

__all__ = ["BashTool", "_validate_command"]
