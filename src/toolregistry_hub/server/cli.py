"""Launcher for the ToolRegistry Hub command line.

The Hub no longer implements its own parser or dispatch.  This module turns
the Hub command line into the equivalent ``toolregistry-server`` command
line, resolves the tool preset, extracts the Hub-only flags, and runs
:class:`toolregistry_server.cli.CLI` with a :class:`HubApp`.

Command mapping:

- ``openapi`` -> ``gateway --openapi``
- ``mcp --transport streamable-http|http`` -> ``gateway --mcp``
- ``mcp --transport sse`` -> ``gateway --sse``
- ``mcp`` (stdio or no transport) -> ``mcp --transport stdio``
- ``gateway``, ``local-hub``, ``hub-shim``, ``keys`` -> unchanged

Usage:
    toolregistry-hub openapi [OPTIONS]
    toolregistry-hub mcp [OPTIONS]
    toolregistry-hub gateway [OPTIONS]
    toolregistry-hub local-hub [OPTIONS]
    toolregistry-hub hub-shim [OPTIONS]
    toolregistry-hub keys [OPTIONS]
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from toolregistry_server.cli import CLI

from .. import __version__
from .app import HubApp
from .registry import _discover_config_path, default_preset_path

#: Environment variable naming the launcher that started a resident hub.
COMMAND_ENV = "TOOLREGISTRY_LOCAL_HUB_COMMAND"

#: Value this launcher reports through :data:`COMMAND_ENV`.
COMMAND_ENV_VALUE = "toolregistry-hub"

#: Warning shown when a detached hub will not be started by this launcher.
DETACHED_HUB_WARNING = (
    "toolregistry-server does not honor TOOLREGISTRY_LOCAL_HUB_COMMAND; if a "
    "detached hub is started, it will run the server CLI with the preset "
    "instead of the Hub launcher, so Hub-only helpers (discovery, "
    "toolcall_reason, admin) will not be applied. Upgrade toolregistry-server "
    "for full support."
)

#: ``local-hub`` options that consume the token that follows them (server 0.9.0).
_LOCAL_HUB_VALUE_OPTIONS = frozenset(
    {
        "--backend",
        "--client-concurrency",
        "--concurrency-timeout",
        "--config",
        "--env",
        "--host",
        "--idle-timeout",
        "--keys-db",
        "--max-body-size",
        "--name",
        "--port",
        "--profile",
        "--regex-timeout",
        "--server-url",
        "--socket",
        "--timeout",
        "--tokens",
    }
)

#: Actions ``local-hub`` accepts; the first one wins as the positional.
_LOCAL_HUB_ACTIONS = ("run", "ensure", "stop", "status")

#: Commands the launcher knows how to translate or pass through.
COMMANDS = ("openapi", "mcp", "gateway", "local-hub", "hub-shim", "keys")

#: Commands whose sub-parser accepts ``--config``.
_CONFIG_COMMANDS = ("openapi", "mcp", "gateway", "local-hub", "hub-shim")


@dataclass
class HubOptions:
    """Hub-only flags, removed from the argv forwarded to the server."""

    admin_port: int | None = None
    """Port for the core admin panel, or ``None`` to disable it."""

    enable_discovery: bool = True
    """Whether to register the tool-discovery helpers."""

    enable_think: bool = True
    """Whether to inject ``toolcall_reason`` into tool schemas."""

    no_banner: bool = False
    """Whether the user asked to suppress the Hub banner."""


def _fail(message: str) -> NoReturn:
    """Print *message* to stderr and exit like argparse does."""
    print(f"toolregistry-hub: error: {message}", file=sys.stderr)
    sys.exit(2)


def _parse_port(value: str) -> int:
    """Parse the ``--admin-port`` value."""
    try:
        return int(value)
    except ValueError:
        _fail(f"argument --admin-port: invalid int value: {value!r}")


def _strip_hub_flags(argv: Sequence[str], options: HubOptions) -> list[str]:
    """Remove the Hub-only flags from *argv* and record their values."""
    kept: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--admin-port":
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                _fail("argument --admin-port: expected one argument")
            options.admin_port = _parse_port(argv[index + 1])
            index += 2
        elif token.startswith("--admin-port="):
            options.admin_port = _parse_port(token.split("=", 1)[1])
            index += 1
        elif token == "--tool-discovery":
            options.enable_discovery = True
            index += 1
        elif token == "--no-tool-discovery":
            options.enable_discovery = False
            index += 1
        elif token == "--think-augment":
            options.enable_think = True
            index += 1
        elif token == "--no-think-augment":
            options.enable_think = False
            index += 1
        elif token == "--no-banner":
            options.no_banner = True
            index += 1
        else:
            kept.append(token)
            index += 1
    return kept


def _find_command(argv: Sequence[str]) -> str | None:
    """Return the first positional token, which names the command."""
    for token in argv:
        if not token.startswith("-"):
            return token
    return None


def _version_requested(argv: Sequence[str]) -> bool:
    """Return whether ``--version`` appears before the command."""
    for token in argv:
        if token in ("-V", "--version"):
            return True
        if not token.startswith("-"):
            return False
    return False


def _help_requested(argv: Sequence[str]) -> bool:
    """Return whether the user asked for help anywhere in the argv."""
    return any(token in ("-h", "--help") for token in argv)


def _help_before_command(argv: Sequence[str]) -> bool:
    """Return whether help was requested before the command token."""
    for token in argv:
        if token in ("-h", "--help"):
            return True
        if not token.startswith("-"):
            return False
    return False


def _take_option(argv: Sequence[str], name: str) -> tuple[str | None, list[str]]:
    """Remove ``name VALUE`` / ``name=VALUE`` from *argv*.

    Returns the last value given and the remaining tokens.  A ``name`` with
    no value is left in place so the server parser reports the error.
    """
    value: str | None = None
    rest: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == name:
            if index + 1 < len(argv):
                value = argv[index + 1]
                index += 2
                continue
            rest.append(token)
            index += 1
        elif token.startswith(name + "="):
            value = token.split("=", 1)[1]
            index += 1
        else:
            rest.append(token)
            index += 1
    return value, rest


def _translate(command: str, rest: Sequence[str]) -> list[str]:
    """Translate one Hub command and its options into a server command.

    The gateway enables every frontend by default (and stored settings can
    re-enable one), so each translated command passes the explicit disables
    for the frontends the Hub command did not ask for.  ``gateway`` keeps the
    server behaviour of serving all three.
    """
    if command == "openapi":
        return ["gateway", "--openapi", "--no-mcp", "--no-sse", *rest]
    if command == "mcp":
        transport, rest = _take_option(rest, "--transport")
        if transport in (None, "stdio"):
            # The gateway has no stdio frontend, and ``--backend`` selects an
            # HTTP backend, so it means nothing on the direct MCP server.
            _backend, rest = _take_option(rest, "--backend")
            return ["mcp", "--transport", "stdio", *rest]
        if transport in ("streamable-http", "http"):
            return ["gateway", "--mcp", "--no-openapi", "--no-sse", *rest]
        if transport == "sse":
            return ["gateway", "--sse", "--no-openapi", "--no-mcp", *rest]
        return ["mcp", "--transport", transport, *rest]
    return [command, *rest]


def _has_option(argv: Sequence[str], name: str) -> bool:
    """Return whether *argv* contains ``name`` or ``name=VALUE``."""
    return any(token == name or token.startswith(name + "=") for token in argv)


def resolve_config_path() -> str:
    """Resolve the tool preset the Hub serves.

    An explicit ``--config`` is handled by the caller; otherwise the same
    discovery order the registry uses applies (``TOOLS_CONFIG``, then a
    ``tools.jsonc``/``tools.yaml``/``tools.yml`` in the working directory),
    falling back to the packaged ``data/tools.yaml`` preset.

    The result is absolute: a discovered candidate is relative to the
    client's working directory, and a detached ``local-hub`` child can
    outlive that directory.
    """
    path = _discover_config_path() or str(default_preset_path())
    return str(Path(path).resolve())


def _inject_config(argv: list[str]) -> list[str]:
    """Add ``--config <preset>`` when the command needs one and none was given."""
    if not argv or argv[0] not in _CONFIG_COMMANDS:
        return argv
    if _has_option(argv, "--config"):
        return argv
    return [*argv, "--config", resolve_config_path()]


def _local_hub_action(rest: Sequence[str]) -> str:
    """Return the ``local-hub`` action, skipping option values.

    argparse reads the first positional as the action, so a value such as
    ``--name ensure`` is not the action.  An unknown positional makes
    argparse fail before anything starts, so it maps to the default.
    """
    index = 0
    while index < len(rest):
        token = rest[index]
        if token in _LOCAL_HUB_VALUE_OPTIONS:
            index += 2
        elif token.startswith("-"):
            index += 1
        else:
            return token if token in _LOCAL_HUB_ACTIONS else "run"
    return "run"


def _detached_hub_requested(command: str, rest: Sequence[str]) -> bool:
    """Return whether *command* may start a hub as a separate process.

    ``local-hub run`` serves in this process with the Hub app, and ``stop``
    and ``status`` never start anything.  ``ensure`` and a ``hub-shim``
    without ``--no-spawn`` delegate the start to the server's ``local_hub``
    module, which spawns the child with the server CLI.
    """
    if command == "local-hub":
        return _local_hub_action(rest) == "ensure"
    if command == "hub-shim":
        return not _has_option(rest, "--no-spawn")
    return False


def _server_reads_command_env() -> bool:
    """Return whether the installed server reads :data:`COMMAND_ENV`."""
    import importlib

    module = importlib.import_module("toolregistry_server.gateway.local_hub")
    return getattr(module, "HUB_COMMAND_ENV", None) is not None


def _warn_about_detached_hub(command: str, rest: Sequence[str]) -> None:
    """Warn when a detached hub will not be started by this launcher."""
    if not _detached_hub_requested(command, rest):
        return
    if _server_reads_command_env():
        return
    print(f"toolregistry-hub: warning: {DETACHED_HUB_WARNING}", file=sys.stderr)


def _hub_help() -> str:
    """Return the top-level Hub usage text."""
    return """\
usage: toolregistry-hub <command> [options]

Pre-configured tool server.  The launcher resolves the tool preset and
forwards the command to toolregistry-server.

commands:
  openapi     Start the OpenAPI frontend (served through the gateway)
  mcp         Start the MCP server (stdio directly; HTTP transports via
              the gateway)
  gateway     Serve OpenAPI and MCP from one process
  local-hub   Run a resident gateway shared by local clients (POSIX only)
  hub-shim    Expose one local hub to a stdio MCP client (POSIX only)
  keys        Manage inbound API keys

hub options (accepted before or after the command):
  --admin-port PORT            Enable the core admin panel on PORT
  --tool-discovery             Enable tool discovery (default)
  --no-tool-discovery          Disable tool discovery
  --think-augment              Enable think-augmented calling (default)
  --no-think-augment           Disable think-augmented calling
  --no-banner                  Do not print the Hub banner
  --version, -V                Show the Hub version

Run 'toolregistry-hub <command> --help' for the options of a command.
"""


def _run_update_check() -> dict | None:
    """Run the async update check synchronously.

    Returns the update info dict, or ``None`` if a running event
    loop is detected or the check fails.
    """
    import asyncio

    from ..version_check import check_for_updates

    try:
        asyncio.get_running_loop()
        return None  # can't block inside an existing loop
    except RuntimeError:
        pass

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(check_for_updates())
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    except Exception:
        return None


def _get_version_string() -> str:
    """Build Hub version string with update check."""
    info = _run_update_check()
    if info is None:
        return f"toolregistry-hub {__version__}"
    if info["update_available"]:
        return (
            f"toolregistry-hub {info['current_version']}\n"
            f"Update available: v{info['latest_version']}\n"
            "Run: pip install --upgrade toolregistry-hub"
        )
    return f"toolregistry-hub {info['current_version']} (Latest)"


def _print_hub_banner() -> None:
    """Print Hub banner with version check."""
    from toolregistry_server.cli import print_banner

    from .banner import BANNER_ART

    info = _run_update_check()
    if info is None:
        version = __version__
        extra_lines = None
    elif info["update_available"]:
        version = info["current_version"]
        extra_lines = [
            f"UPDATE AVAILABLE: v{info['latest_version']}",
            "Run: pip install --upgrade toolregistry-hub",
        ]
    else:
        version = f"{info['current_version']} (Latest)"
        extra_lines = None

    print_banner(version=version, banner_art=BANNER_ART, extra_lines=extra_lines)


def main(args: list[str] | None = None) -> NoReturn | None:
    """Run the Hub launcher.

    Args:
        args: Command-line arguments, excluding the program name.  Defaults
            to ``sys.argv[1:]``.

    Returns:
        ``None`` on success, or whatever the server CLI returns.
    """
    argv = list(sys.argv[1:] if args is None else args)
    options = HubOptions()
    argv = _strip_hub_flags(argv, options)

    if _version_requested(argv):
        print(_get_version_string())
        return None

    if _help_before_command(argv):
        print(_hub_help())
        return None

    command = _find_command(argv)
    if command is None:
        print(_hub_help())
        return None

    rest = argv[argv.index(command) + 1 :]
    translated = _inject_config(_translate(command, rest))
    # The Hub prints its own banner; the server must not print a second one.
    translated.insert(0, "--no-banner")

    os.environ[COMMAND_ENV] = COMMAND_ENV_VALUE

    if not options.no_banner and not _help_requested(argv):
        _print_hub_banner()

    _warn_about_detached_hub(command, rest)

    app = HubApp(
        enable_discovery=options.enable_discovery,
        enable_think=options.enable_think,
        admin_port=options.admin_port,
    )
    return CLI(app=app).main(translated)


if __name__ == "__main__":
    main()
