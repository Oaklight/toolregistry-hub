"""Outbound URL policy for the fetch tool.

The address decision belongs to :mod:`toolregistry.netpolicy`; this module
adds only the rules the hub owns:

* ``fetch`` accepts ``http`` and ``https`` only.  The core policy also allows
  the MCP WebSocket schemes, which the fetch tool must not dial.
* A refusal is reported as :class:`URLPolicyError` with a short reason, which
  ``fetch.py`` maps to ``FetchPolicyError`` and logs without an address.

Resolution, the address-class checks, the NAT64 / transition-range refusals
and the success cache all live in the core module.  The hub no longer keeps a
copy, so the two cannot drift.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from toolregistry.netpolicy import (
    PrivateAddressError,
    UnsafeAddressError,
    validate_outbound_url,
)

__all__ = [
    "URLPolicyError",
    "validate_fetch_request",
    "validate_proxy_url",
    "validate_target_url",
]

_ALLOWED_SCHEMES = frozenset({"http", "https"})


class URLPolicyError(ValueError):
    """Raised when a URL or proxy violates the hub's outbound policy.

    Attributes:
        reason: Short category for logs: ``"scheme"``, ``"host"``,
            ``"dns"`` or ``"non-public"``.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _check_syntax(value: str, *, kind: str) -> None:
    """Refuse an empty, malformed, hostless or non-http(s) URL."""
    if not isinstance(value, str) or not value.strip():
        raise URLPolicyError(f"{kind} URL is empty", reason="host")
    try:
        parsed = urlsplit(value.strip())
        scheme = parsed.scheme.lower()
        host = parsed.hostname
        # Accessing ``.port`` raises ValueError for a non-numeric port.
        _ = parsed.port
    except ValueError as exc:
        raise URLPolicyError(f"{kind} URL is not valid", reason="host") from exc
    if scheme not in _ALLOWED_SCHEMES:
        raise URLPolicyError(
            f"{kind} scheme {scheme!r} is not allowed (only http/https)",
            reason="scheme",
        )
    if not host:
        raise URLPolicyError(f"{kind} URL has no host", reason="host")


def _validate(value: str, *, kind: str, allow_private_hosts: bool) -> str:
    """Check the hub-owned rules, then delegate the address decision."""
    _check_syntax(value, kind=kind)
    try:
        return validate_outbound_url(value, allow_private_hosts=allow_private_hosts)
    except PrivateAddressError as exc:
        raise URLPolicyError(str(exc), reason="non-public") from exc
    except UnsafeAddressError as exc:
        raise URLPolicyError(str(exc), reason="dns") from exc


def validate_target_url(url: str, *, allow_private_hosts: bool = False) -> str:
    """Validate a caller-supplied URL before any I/O.

    Args:
        url: URL to fetch.
        allow_private_hosts: Skip the address-class checks.  The scheme is
            always restricted to http/https.

    Returns:
        The unchanged URL when it is allowed.

    Raises:
        URLPolicyError: If the scheme or the destination is not allowed.
    """
    return _validate(url, kind="URL", allow_private_hosts=allow_private_hosts)


def validate_proxy_url(proxy: str, *, allow_private_hosts: bool = False) -> str:
    """Validate a caller-supplied proxy URL before any I/O.

    Args:
        proxy: Proxy URL.
        allow_private_hosts: Skip the address-class checks.  The scheme is
            always restricted to http/https.

    Returns:
        The unchanged proxy URL when it is allowed.

    Raises:
        URLPolicyError: If the scheme or the destination is not allowed.
    """
    return _validate(proxy, kind="proxy", allow_private_hosts=allow_private_hosts)


def validate_fetch_request(
    url: str,
    proxy: str | None = None,
    *,
    allow_private_hosts: bool = False,
) -> None:
    """Validate the target and, when given, the proxy of one fetch request.

    Raises:
        URLPolicyError: If either URL is not allowed.
    """
    validate_target_url(url, allow_private_hosts=allow_private_hosts)
    if proxy is not None:
        validate_proxy_url(proxy, allow_private_hosts=allow_private_hosts)
