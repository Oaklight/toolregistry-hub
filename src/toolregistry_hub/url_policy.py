"""Outbound URL policy for the fetch tool.

The hub fetches URLs supplied by every caller of the tool, so each URL and
each caller-supplied proxy must be checked before any connection is made.
This module is deliberately stdlib-only and self-contained: ``toolregistry-hub``
supports core releases that predate the library-level net policy, so the hub
cannot import it yet.  When the supported core floor includes that module,
this file can be replaced by a thin wrapper.

Policy:

* Only ``http`` and ``https`` are allowed, for both targets and proxies.
* Every address a host resolves to must be globally routable.  A host that
  resolves to a mix of public and private addresses is refused, because the
  HTTP client may pick either one.
* Resolution failures are refused (fail closed).
* IPv4-mapped IPv6 addresses are unwrapped first, and the IPv4 address
  embedded in a NAT64 prefix is checked as an IPv4 address, because
  ``ipaddress.is_global`` treats both as globally routable.
* Transition, documentation, benchmarking, multicast and other special
  purpose ranges are refused explicitly where ``is_global`` reports them as
  reachable.

Operators can allow private destinations with ``allow_private_hosts=True``.
That skips only the address-class checks; both schemes stay restricted.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

__all__ = [
    "URLPolicyError",
    "validate_fetch_request",
    "validate_proxy_url",
    "validate_target_url",
]

_ALLOWED_SCHEMES = frozenset({"http", "https"})

# Ranges that ``ipaddress.is_global`` reports as reachable on at least one
# supported Python version, but that must never be dialed.  Copied from
# veilrender's validator so both projects make the same decision.
_SPECIAL_PURPOSE_NETWORKS = tuple(
    ipaddress.ip_network(net)
    for net in (
        "192.0.0.0/24",  # IETF protocol assignments
        "192.88.99.0/24",  # 6to4 relay anycast (deprecated)
        "198.18.0.0/15",  # benchmarking
        "240.0.0.0/4",  # reserved, incl. broadcast
        "64:ff9b:1::/48",  # local-use NAT64
        "::/96",  # IPv4-compatible (deprecated)
        "100::/64",  # discard-only
        "2001::/32",  # Teredo (embeds IPv4)
        "2001:2::/48",  # benchmarking
        "2001:10::/28",  # ORCHID
        "2001:20::/28",  # ORCHIDv2
        "2001:db8::/32",  # documentation
        "2002::/16",  # 6to4 (embeds IPv4)
        "3fff::/20",  # documentation
        "5f00::/16",  # SRv6 SIDs
    )
)

_NAT64_WELL_KNOWN = ipaddress.ip_network("64:ff9b::/96")


class URLPolicyError(ValueError):
    """Raised when a URL or proxy violates the outbound address policy.

    Attributes:
        reason: Short category for logs: ``"scheme"``, ``"host"``,
            ``"dns"``, ``"non-public"`` or ``"proxy"``.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _normalize_host(host: str) -> str:
    """Strip brackets, a trailing root dot and case from a URL host."""
    host = host.strip()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    return host.rstrip(".").lower()


def _unwrap_ipv4_mapped(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Return the embedded IPv4 address for an IPv4-mapped IPv6 address."""
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        return addr.ipv4_mapped
    return addr


def _embedded_ipv4(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> ipaddress.IPv4Address | None:
    """Return the IPv4 address encoded in an IPv6 transition prefix."""
    if not isinstance(addr, ipaddress.IPv6Address):
        return None
    if addr.ipv4_mapped is not None:
        return addr.ipv4_mapped
    if addr in _NAT64_WELL_KNOWN:
        return ipaddress.IPv4Address(int(addr) & 0xFFFFFFFF)
    return None


def _is_blocked_address(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    """Return True if the address is outside the globally routable space."""
    embedded = _embedded_ipv4(addr)
    if embedded is not None:
        addr = embedded

    if (
        addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
        or addr.is_link_local
        or addr.is_loopback
    ):
        return True
    if not addr.is_global:
        return True
    return any(
        addr in net for net in _SPECIAL_PURPOSE_NETWORKS if net.version == addr.version
    )


def _resolve(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Resolve *host* to addresses, refusing failure and empty answers.

    Raises:
        URLPolicyError: If *host* cannot be resolved.
    """
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        return [_unwrap_ipv4_mapped(literal)]

    try:
        infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError, OSError) as exc:
        raise URLPolicyError(
            f"could not resolve host {host!r}",
            reason="dns",
        ) from exc

    addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for _family, _type, _proto, _canonname, sockaddr in infos:
        # A link-local IPv6 sockaddr can carry a scope id; it is not part of
        # the address and would make ``ip_address`` fail.
        text = str(sockaddr[0]).split("%", 1)[0]
        try:
            addresses.append(ipaddress.ip_address(text))
        except ValueError as exc:
            raise URLPolicyError(
                f"could not resolve host {host!r}",
                reason="dns",
            ) from exc

    if not addresses:
        raise URLPolicyError(f"could not resolve host {host!r}", reason="dns")
    return [_unwrap_ipv4_mapped(addr) for addr in addresses]


def _require_public_addresses(host: str, *, kind: str) -> None:
    """Refuse *host* unless every resolved address is globally routable.

    Args:
        host: Normalized hostname or IP literal.
        kind: ``"host"`` or ``"proxy host"`` for the error message.

    Raises:
        URLPolicyError: If any address is blocked, with the resolved address
            intentionally omitted from the message.
    """
    for addr in _resolve(host):
        if _is_blocked_address(addr):
            raise URLPolicyError(
                f"{kind} {host!r} is not a public address; "
                "set allow_private_hosts=True to allow private destinations",
                reason="non-public",
            )


def _parse_url(value: str, *, kind: str) -> tuple[str, str]:
    """Return ``(scheme, host)`` for *value*, or raise URLPolicyError."""
    if not isinstance(value, str) or not value.strip():
        raise URLPolicyError(f"{kind} URL is empty", reason="host")
    try:
        parsed = urlsplit(value.strip())
        scheme = parsed.scheme.lower()
        host = _normalize_host(parsed.hostname or "")
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
    return scheme, host


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
    _scheme, host = _parse_url(url, kind="URL")
    if not allow_private_hosts:
        _require_public_addresses(host, kind="host")
    return url


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
    _scheme, host = _parse_url(proxy, kind="proxy")
    if not allow_private_hosts:
        _require_public_addresses(host, kind="proxy host")
    return proxy


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
