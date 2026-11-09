"""Capability detection for the installed ``toolregistry-server``.

The Hub supports a released server floor.  The runtime source manager and
the gateway are newer than that floor, so the launcher chooses a path once,
at import, and the rest of the package reads these flags instead of probing
the installed package again.
"""

from __future__ import annotations

import importlib.util

#: ``toolregistry_server.source_manager.SourceManager`` is available.
SERVER_HAS_SOURCE_MANAGER = (
    importlib.util.find_spec("toolregistry_server.source_manager") is not None
)

#: ``toolregistry_server.gateway.GatewayAdapter`` is available.
SERVER_HAS_GATEWAY = importlib.util.find_spec("toolregistry_server.gateway") is not None


__all__ = ["SERVER_HAS_GATEWAY", "SERVER_HAS_SOURCE_MANAGER"]
