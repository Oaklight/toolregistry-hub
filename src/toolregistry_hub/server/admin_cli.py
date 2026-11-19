"""Standalone admin panel for the Hub, with the kanban tab.

``toolregistry-hub admin`` serves the core admin panel from its own process
so a long-lived panel does not share the MCP server's lifetime.  The board
store is resolved with the same function the MCP tool uses, so both
processes open one SQLite file.

Usage::

    toolregistry-hub admin --port 8081 --token-file ~/.config/.../admin-token
"""

from __future__ import annotations

import argparse
import contextlib
import ipaddress
import signal
import sys
import threading
from pathlib import Path

from .._vendor.structlog import get_logger
from .registry import build_registry

logger = get_logger()

#: Default bind address.  The panel serves a writable board, so it listens on
#: loopback unless the operator asks otherwise.
DEFAULT_HOST = "127.0.0.1"

#: Default port, matching the core admin panel.
DEFAULT_PORT = 8081


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``admin`` subcommand parser."""
    parser = argparse.ArgumentParser(
        prog="toolregistry-hub admin",
        description=(
            "Serve the ToolRegistry admin panel and the kanban tab from a "
            "standalone process."
        ),
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port")
    parser.add_argument("--token", default=None, help="Panel bearer token")
    parser.add_argument(
        "--token-file",
        default=None,
        help="Read the panel bearer token from the first non-empty line",
    )
    parser.add_argument(
        "--config", default=None, help="Tool config/preset path to load"
    )
    parser.add_argument(
        "--db", default=None, help="Board SQLite path (shared with the MCP tool)"
    )
    parser.add_argument(
        "--no-banner", action="store_true", help="Do not print the Hub banner"
    )
    return parser


def _read_token(args: argparse.Namespace) -> str | None:
    """Resolve the panel token from the flags.

    Args:
        args: The parsed arguments.

    Returns:
        The token, or ``None`` when neither flag was given.

    Raises:
        SystemExit: If both flags are given, or the token file is empty.
    """
    if args.token and args.token_file:
        print(
            "toolregistry-hub: error: pass --token or --token-file, not both",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if args.token:
        return args.token
    if not args.token_file:
        return None
    path = Path(args.token_file).expanduser()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip()
    except OSError as exc:
        print(
            f"toolregistry-hub: error: cannot read token file: {exc}", file=sys.stderr
        )
        raise SystemExit(2) from exc
    print(f"toolregistry-hub: error: token file is empty: {path}", file=sys.stderr)
    raise SystemExit(2)


def _is_loopback(host: str) -> bool:
    """Return whether *host* names the loopback interface."""
    if host in {"localhost", "::1"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def run_admin(
    argv: list[str] | None = None,
    *,
    stop_event: threading.Event | None = None,
) -> int:
    """Run the standalone admin panel until a signal arrives.

    Args:
        argv: Arguments after the ``admin`` command.  Defaults to
            ``sys.argv[2:]``.
        stop_event: Event that ends the wait loop.  Tests pre-set it instead
            of sending a signal.

    Returns:
        The process exit code.

    Raises:
        SystemExit: If the arguments or the token configuration are invalid.
    """
    args = _build_parser().parse_args(argv)
    token = _read_token(args)
    if token is None and not _is_loopback(args.host):
        print(
            "toolregistry-hub: error: a bearer token is required when the "
            f"panel listens on {args.host!r}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    from ..board.admin import BoardAdminExtension
    from ..board.paths import resolve_db_path

    registry = build_registry(
        tools_config_path=args.config,
        enable_discovery=False,
        enable_think=False,
    )
    registry.enable_logging()
    db_path = resolve_db_path(args.db)
    extension = BoardAdminExtension(db=db_path, expose_path=_is_loopback(args.host))
    info = registry.enable_admin(
        host=args.host,
        port=args.port,
        auth_token=token,
        extensions=[extension],
    )
    logger.info(f"Admin panel at {info.url}")
    logger.info(f"Board database: {db_path}")
    print(f"Admin panel: {info.url}", flush=True)
    print(f"Board database: {db_path}", flush=True)
    if token:
        print("Bearer token: configured", flush=True)

    event = stop_event or threading.Event()

    def _stop(*_: object) -> None:
        event.set()

    previous = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        # Signal handlers can only be installed from the main thread; the
        # tests call this from a worker, where the wait loop is driven by the
        # injected event instead.
        with contextlib.suppress(ValueError):
            previous[sig] = signal.signal(sig, _stop)
    try:
        event.wait()
    finally:
        registry.disable_admin()
        for sig, handler in previous.items():
            with contextlib.suppress(ValueError):
                signal.signal(sig, handler)
    return 0


__all__ = ["DEFAULT_HOST", "DEFAULT_PORT", "run_admin"]
