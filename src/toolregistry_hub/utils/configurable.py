"""Configurable protocol for tool classes.

This module defines a protocol for classes that can report their
configuration readiness. Used by ``build_registry()`` to determine
whether to auto-disable a tool.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Configurable(Protocol):
    """Protocol for classes that can report their configuration readiness.

    Any class implementing ``is_configured()`` automatically satisfies this
    protocol — no explicit inheritance required (structural subtyping).

    Used by ``build_registry()`` to determine whether to auto-disable a tool
    when its required configuration (API keys, URLs, etc.) is missing.
    """

    def is_configured(self) -> bool:
        """Check if the instance has valid configuration to operate.

        Returns:
            True if the instance is properly configured, False otherwise.
        """
        ...
