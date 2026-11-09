"""Tool metadata declarations, re-exported from the core package.

Hub declares tags, ``defer``, hints and output schemas on each tool method
with the core ``@tool_metadata`` decorator.  The dependency floor is
``toolregistry>=0.21.0``, which provides the decorator, so there is no
Hub-side fallback to keep in sync.

``copy_declaration`` is the name the rewriting helpers use (annotation
narrowing and ``Literal`` binding rebuild the function object); it is the
core :func:`toolregistry.copy_tool_metadata`.
"""

from toolregistry import copy_tool_metadata, tool_metadata

#: Copy a declaration onto a rebuilt function object.
copy_declaration = copy_tool_metadata

__all__ = ["copy_declaration", "tool_metadata"]
