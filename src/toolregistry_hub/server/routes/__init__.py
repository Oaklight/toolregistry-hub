"""Routes module.

Only the version router remains; all tool routes are now auto-generated
by the autoroute module from the central ToolRegistry.
"""

from .version import router as version_router

__all__ = ["version_router"]
