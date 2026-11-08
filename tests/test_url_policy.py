"""Tests for the fetch outbound address policy."""

import socket
from unittest.mock import patch

import pytest

from toolregistry_hub.url_policy import (
    URLPolicyError,
    validate_fetch_request,
    validate_proxy_url,
    validate_target_url,
)


def _addrinfo(*addresses: str) -> list[tuple]:
    """Build minimal ``getaddrinfo`` results for *addresses*."""
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 0))
        for address in addresses
    ]


# ============================================================
# Blocked address classes
# ============================================================


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "127.1.2.3",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "0.0.0.0",
        "224.0.0.1",
        "198.18.0.1",
        "240.0.0.1",
        "[::1]",
        "[::]",
        "[fe80::1]",
        "[::ffff:127.0.0.1]",
        "[64:ff9b::7f00:1]",
        "[64:ff9b:1::1]",
        "[2002:7f00:1::]",
        "[2001::1]",
        "[2001:10::1]",
        "[2001:db8::1]",
        "[3fff::1]",
    ],
)
def test_private_and_special_addresses_are_refused(host: str) -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_target_url(f"http://{host}/")
    assert exc.value.reason == "non-public"


@pytest.mark.parametrize(
    "url",
    [
        "http://93.184.216.34/",
        "https://[2606:2800:220:1:248:1893:25c8:1946]/",
    ],
)
def test_public_literal_addresses_are_allowed(url: str) -> None:
    assert validate_target_url(url) == url


# ============================================================
# Scheme, host and syntax checks
# ============================================================


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "data:text/plain,hello",
        "ftp://example.com/file",
        "javascript:alert(1)",
        "ws://example.com/socket",
    ],
)
def test_non_http_schemes_are_refused(url: str) -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_target_url(url)
    assert exc.value.reason == "scheme"
    assert "only http/https" in str(exc.value)


@pytest.mark.parametrize(
    "url",
    [
        "http:///no-host",
        "http://",
        "https://:443/",
    ],
)
def test_missing_host_is_refused(url: str) -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_target_url(url)
    assert exc.value.reason == "host"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:not-a-port/",
        "http://[::1/",
    ],
)
def test_malformed_urls_are_refused(url: str) -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_target_url(url)
    assert exc.value.reason == "host"


# ============================================================
# DNS behaviour
# ============================================================


def test_trailing_dot_host_is_normalized() -> None:
    with patch(
        "toolregistry_hub.url_policy.socket.getaddrinfo",
        return_value=_addrinfo("93.184.216.34"),
    ) as resolve:
        assert validate_target_url("http://Example.COM./page") == (
            "http://Example.COM./page"
        )
    assert resolve.call_args.args[0] == "example.com"


def test_dns_failure_is_refused() -> None:
    with (
        patch(
            "toolregistry_hub.url_policy.socket.getaddrinfo",
            side_effect=socket.gaierror("no such host"),
        ),
        pytest.raises(URLPolicyError) as exc,
    ):
        validate_target_url("http://missing.example/")
    assert exc.value.reason == "dns"


def test_empty_dns_answer_is_refused() -> None:
    with (
        patch(
            "toolregistry_hub.url_policy.socket.getaddrinfo",
            return_value=[],
        ),
        pytest.raises(URLPolicyError) as exc,
    ):
        validate_target_url("http://empty.example/")
    assert exc.value.reason == "dns"


def test_any_private_answer_refuses_the_host() -> None:
    with (
        patch(
            "toolregistry_hub.url_policy.socket.getaddrinfo",
            return_value=_addrinfo("93.184.216.34", "10.0.0.7"),
        ),
        pytest.raises(URLPolicyError) as exc,
    ):
        validate_target_url("http://mixed.example/")
    assert exc.value.reason == "non-public"


def test_error_does_not_leak_the_resolved_address() -> None:
    with (
        patch(
            "toolregistry_hub.url_policy.socket.getaddrinfo",
            return_value=_addrinfo("10.1.2.3"),
        ),
        pytest.raises(URLPolicyError) as exc,
    ):
        validate_target_url("http://internal.example/")
    message = str(exc.value)
    assert "allow_private_hosts" in message
    assert "10.1.2.3" not in message


# ============================================================
# Proxy policy
# ============================================================


def test_public_proxy_is_allowed() -> None:
    with patch(
        "toolregistry_hub.url_policy.socket.getaddrinfo",
        return_value=_addrinfo("93.184.216.34"),
    ):
        assert validate_proxy_url("http://proxy.example:3128") == (
            "http://proxy.example:3128"
        )


def test_private_proxy_is_refused() -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_proxy_url("http://127.0.0.1:3128")
    assert exc.value.reason == "non-public"
    assert "allow_private_hosts" in str(exc.value)


@pytest.mark.parametrize(
    "proxy",
    [
        "socks5://proxy.example:1080",
        "socks5h://proxy.example:1080",
        "file:///tmp/socket",
    ],
)
def test_non_http_proxy_schemes_are_refused(proxy: str) -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_proxy_url(proxy)
    assert exc.value.reason == "scheme"


def test_proxy_without_host_is_refused() -> None:
    with pytest.raises(URLPolicyError) as exc:
        validate_proxy_url("http://")
    assert exc.value.reason == "host"


# ============================================================
# Operator opt-in
# ============================================================


def test_opt_in_allows_private_targets_and_proxies() -> None:
    assert validate_target_url("http://127.0.0.1/", allow_private_hosts=True) == (
        "http://127.0.0.1/"
    )
    assert (
        validate_proxy_url("http://10.0.0.5:3128", allow_private_hosts=True)
        == "http://10.0.0.5:3128"
    )


@pytest.mark.parametrize(
    ("call", "value"),
    [
        (validate_target_url, "file:///etc/passwd"),
        (validate_proxy_url, "socks5://127.0.0.1:1080"),
    ],
)
def test_opt_in_keeps_scheme_checks(call, value: str) -> None:
    with pytest.raises(URLPolicyError) as exc:
        call(value, allow_private_hosts=True)
    assert exc.value.reason == "scheme"


# ============================================================
# Combined request check
# ============================================================


def test_request_checks_target_then_proxy() -> None:
    with pytest.raises(URLPolicyError):
        validate_fetch_request("http://127.0.0.1/", "http://127.0.0.1:3128")

    with (
        patch(
            "toolregistry_hub.url_policy.socket.getaddrinfo",
            return_value=_addrinfo("93.184.216.34"),
        ),
        pytest.raises(URLPolicyError) as exc,
    ):
        validate_fetch_request("http://example.com/", "http://127.0.0.1:3128")
    assert exc.value.reason == "non-public"


def test_request_without_proxy_validates_only_the_target() -> None:
    with patch(
        "toolregistry_hub.url_policy.socket.getaddrinfo",
        return_value=_addrinfo("93.184.216.34"),
    ):
        validate_fetch_request("http://example.com/")
