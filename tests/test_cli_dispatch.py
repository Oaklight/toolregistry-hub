"""Tests for HubCLI argument routing.

The Hub builds ``serve_mcp``/``serve_openapi`` kwargs explicitly instead of
forwarding the parsed namespace, so a flag added to the server subparser is
dropped unless the Hub passes it on (#78).
"""

import argparse
from unittest.mock import patch

import pytest

from toolregistry_hub.server.cli import HubCLI


def _mcp_namespace(**overrides) -> argparse.Namespace:
    """Return a parsed-namespace stand-in for ``hub mcp``."""
    values = {
        "command": "mcp",
        "transport": "http",
        "host": "0.0.0.0",
        "port": 8000,
        "config": "tools.jsonc",
        "tool_discovery": True,
        "think_augment": True,
        "profile": None,
        "admin_port": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class TestMCPDispatch:
    """``hub mcp`` kwargs reach the Hub app intact."""

    def test_forwards_server_url(self):
        """--server-url reaches serve_mcp so metadata names the public origin."""
        cli = HubCLI()
        parsed = _mcp_namespace(server_url="https://hub.example.com/mcp")

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        assert (
            mock_serve.call_args.kwargs["server_url"] == "https://hub.example.com/mcp"
        )

    def test_defaults_server_url_to_none(self):
        """A namespace without the attribute still dispatches (older server)."""
        cli = HubCLI()
        parsed = _mcp_namespace()

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        assert mock_serve.call_args.kwargs["server_url"] is None

    def test_forwards_cache_hints(self):
        """tools/list cache flags reach serve_mcp instead of being dropped (#83)."""
        cli = HubCLI()
        parsed = _mcp_namespace(tools_list_ttl_ms=0, tools_list_cache_scope="public")

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        kwargs = mock_serve.call_args.kwargs
        assert kwargs["tools_list_ttl_ms"] == 0
        assert kwargs["tools_list_cache_scope"] == "public"

    def test_cache_hints_default_to_none(self):
        """A namespace without the attributes still dispatches (older server)."""
        cli = HubCLI()
        parsed = _mcp_namespace()

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        kwargs = mock_serve.call_args.kwargs
        assert kwargs["tools_list_ttl_ms"] is None
        assert kwargs["tools_list_cache_scope"] is None

    def test_forwards_transport_and_host(self):
        """The kwargs the Hub already passed are unaffected."""
        cli = HubCLI()
        parsed = _mcp_namespace(
            transport="streamable-http", host="127.0.0.1", port=9100
        )

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        kwargs = mock_serve.call_args.kwargs
        assert kwargs["transport"] == "streamable-http"
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 9100
        assert kwargs["profile"] is None

    def test_subparser_accepts_server_url(self):
        """The flag is available on the Hub's mcp subcommand."""
        parser = HubCLI().create_parser()
        try:
            parsed = parser.parse_args(
                ["mcp", "--server-url", "https://hub.example.com/mcp"]
            )
        except SystemExit:  # pragma: no cover - depends on the installed server
            pytest.skip("installed toolregistry-server predates --server-url")

        assert parsed.server_url == "https://hub.example.com/mcp"
