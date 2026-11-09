"""Tests for HubCLI argument routing.

The Hub builds its serving kwargs explicitly instead of forwarding the
parsed namespace, so a flag added to a server subparser is dropped unless
the Hub passes it on (#78).  ``openapi`` and the HTTP MCP transports go
through the gateway; ``mcp --transport stdio`` uses the direct MCP server.
"""

import argparse
from unittest.mock import patch

import pytest

from toolregistry_hub.server.cli import HubCLI


def _mcp_namespace(**overrides) -> argparse.Namespace:
    """Return a parsed-namespace stand-in for ``hub mcp --transport stdio``."""
    values = {
        "command": "mcp",
        "transport": "stdio",
        "host": "0.0.0.0",
        "port": 8000,
        "config": "tools.jsonc",
        "tool_discovery": True,
        "think_augment": True,
        "profile": None,
        "admin_port": None,
        "config_reload": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class TestMCPDispatch:
    """``hub mcp --transport stdio`` kwargs reach the Hub app intact."""

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
        """A namespace without the attribute still dispatches."""
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
        """A namespace without the attributes still dispatches."""
        cli = HubCLI()
        parsed = _mcp_namespace()

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        kwargs = mock_serve.call_args.kwargs
        assert kwargs["tools_list_ttl_ms"] is None
        assert kwargs["tools_list_cache_scope"] is None

    def test_forwards_config_reload(self):
        """--config-reload reaches the server so its watcher can start."""
        cli = HubCLI()
        parsed = _mcp_namespace(config_reload=True)

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        assert mock_serve.call_args.kwargs["config_reload"] is True

    def test_config_reload_defaults_off(self):
        """Hot reload stays off unless the flag is passed (#144)."""
        cli = HubCLI()
        parsed = _mcp_namespace()

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        assert mock_serve.call_args.kwargs["config_reload"] is False

    def test_forwards_transport_and_host(self):
        """The kwargs the Hub already passed are unaffected."""
        cli = HubCLI()
        parsed = _mcp_namespace(host="127.0.0.1", port=9100)

        with patch.object(type(cli.app), "serve_mcp") as mock_serve:
            cli.dispatch(parsed)

        kwargs = mock_serve.call_args.kwargs
        assert kwargs["transport"] == "stdio"
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 9100
        assert kwargs["profile"] is None

    @pytest.mark.parametrize("transport", ["streamable-http", "http", "sse"])
    def test_http_transports_use_the_gateway(self, transport):
        cli = HubCLI()
        parsed = _mcp_namespace(transport=transport)

        with patch.object(type(cli.app), "serve_gateway") as mock_serve:
            cli.dispatch(parsed)

        assert mock_serve.call_args.kwargs["openapi_enabled"] is False

    def test_subparser_accepts_server_url(self):
        """The flag is available on the Hub's mcp subcommand."""
        parser = HubCLI().create_parser()
        parsed = parser.parse_args(
            ["mcp", "--server-url", "https://hub.example.com/mcp"]
        )

        assert parsed.server_url == "https://hub.example.com/mcp"


def _openapi_namespace(**overrides) -> argparse.Namespace:
    """Return a parsed-namespace stand-in for ``hub openapi``."""
    values = {
        "command": "openapi",
        "host": "0.0.0.0",
        "port": 8000,
        "config": "tools.jsonc",
        "tool_discovery": True,
        "think_augment": True,
        "profile": None,
        "admin_port": None,
        "config_reload": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class TestOpenAPIDispatch:
    """``hub openapi`` kwargs reach the gateway intact."""

    def test_forwards_backend(self):
        """--backend reaches serve_gateway instead of being dropped."""
        cli = HubCLI()
        parsed = _openapi_namespace(backend="httpserver")

        with patch.object(type(cli.app), "serve_gateway") as mock_serve:
            cli.dispatch(parsed)

        assert mock_serve.call_args.kwargs["backend"] == "httpserver"
        assert mock_serve.call_args.kwargs["openapi_enabled"] is True

    def test_backend_defaults_to_fastapi(self):
        """A namespace without the attribute keeps the server default."""
        cli = HubCLI()
        parsed = _openapi_namespace()

        with patch.object(type(cli.app), "serve_gateway") as mock_serve:
            cli.dispatch(parsed)

        assert mock_serve.call_args.kwargs["backend"] == "fastapi"

    def test_subparser_accepts_backend(self):
        """The flag is available on the Hub's openapi subcommand."""
        parser = HubCLI().create_parser()
        parsed = parser.parse_args(["openapi", "--backend", "httpserver"])

        assert parsed.backend == "httpserver"
