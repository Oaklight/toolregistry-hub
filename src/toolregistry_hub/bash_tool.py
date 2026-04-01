"""Shell command execution tool with built-in safety validation.

Provides a ``BashTool.execute()`` method that runs shell commands via
``subprocess.run``.  A static deny list blocks known-dangerous patterns
(recursive delete, privilege escalation, fork bombs, etc.) before the
subprocess is spawned.

When the upstream ``toolregistry`` package exposes ``ToolMetadata`` and
``ToolTag``, they are imported lazily so that this module still works
standalone without the upstream dependency.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# Maximum bytes kept for stdout / stderr to prevent memory exhaustion.
_MAX_OUTPUT_BYTES = 65_536  # 64 KB

# ---------------------------------------------------------------------------
# Danger-pattern deny list
# ---------------------------------------------------------------------------
# Each entry is (compiled_regex, human-readable reason).
# Patterns are checked against *each segment* of the command after splitting
# on shell operators (&&, ||, ;, |).

_DANGER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # -- Destructive filesystem operations --
    (
        re.compile(
            r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+[/~*]"
            r"|\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+[/~*]"
        ),
        "Recursive forced deletion of root, home, or wildcard paths",
    ),
    (re.compile(r"\bmkfs\b"), "Filesystem formatting"),
    (re.compile(r"\bdd\s+.*\bif="), "Raw disk image write"),
    (re.compile(r">\s*/dev/sd[a-z]"), "Device overwrite"),
    # -- Privilege escalation --
    (re.compile(r"\bsudo\b"), "Privilege escalation via sudo"),
    (re.compile(r"\bsu\s+-"), "User switching via su"),
    (
        re.compile(r"\bchmod\s+.*-[a-zA-Z]*R.*\b777\b.*\s+/"),
        "Recursive world-writable permission on root",
    ),
    (re.compile(r"\bchown\s+.*-[a-zA-Z]*R"), "Recursive ownership change"),
    # -- Code injection --
    (re.compile(r"\beval\b"), "Arbitrary code evaluation"),
    (re.compile(r"\bexec\b"), "Process replacement via exec"),
    # -- Fork bomb --
    (re.compile(r":\(\)\s*\{.*:\|:.*\}"), "Fork bomb"),
    # -- Git destructive operations --
    (re.compile(r"\bgit\s+push\s+.*--force\b"), "Force push"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "Hard reset"),
    (re.compile(r"\bgit\s+clean\s+.*-[a-zA-Z]*f"), "Force clean"),
    # -- System control --
    (re.compile(r"\bshutdown\b"), "System shutdown"),
    (re.compile(r"\breboot\b"), "System reboot"),
    (re.compile(r"\bhalt\b"), "System halt"),
    (re.compile(r"\bkill\s+.*-9\s+1\b"), "Killing init process"),
]

# Pipe-to-shell: checked on the full (unsplit) command.
_PIPE_EXEC_RE = re.compile(r"\b(?:curl|wget)\b.*\|\s*(?:bash|sh|zsh|dash)\b")

# Shell operator split (&&, ||, ;, |) — simplistic but sufficient for the
# deny-list use-case.  We do NOT attempt full AST parsing.
_OPERATOR_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;)\s*")


def _validate_command(command: str) -> None:
    """Raise ``ValueError`` if *command* matches a known-dangerous pattern.

    Args:
        command: Raw shell command string.

    Raises:
        ValueError: With a human-readable reason describing why the command
            was rejected.
    """
    # 1. Pipe-to-shell check on the full command
    if _PIPE_EXEC_RE.search(command):
        raise ValueError("Dangerous command blocked: pipe-to-shell execution detected")

    # 2. Segment by shell operators and check each part
    segments = _OPERATOR_SPLIT_RE.split(command)
    for segment in segments:
        stripped = segment.strip()
        if not stripped:
            continue
        for pattern, reason in _DANGER_PATTERNS:
            if pattern.search(stripped):
                raise ValueError(f"Dangerous command blocked: {reason}")


def _truncate(text: str, max_bytes: int = _MAX_OUTPUT_BYTES) -> str:
    """Truncate *text* to at most *max_bytes* UTF-8 bytes.

    If truncation occurs, a marker is appended so the caller knows the
    output was clipped.

    Args:
        text: The string to truncate.
        max_bytes: Maximum number of UTF-8 bytes allowed.

    Returns:
        The (possibly truncated) string.
    """
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n... [output truncated]"


# ---------------------------------------------------------------------------
# Lazy upstream ToolMetadata (optional)
# ---------------------------------------------------------------------------
try:
    from toolregistry import ToolMetadata, ToolTag

    _metadata = ToolMetadata(
        tags={ToolTag.DESTRUCTIVE, ToolTag.PRIVILEGED},
        locality="local",
        timeout=120.0,
    )
except Exception:  # ImportError or missing attrs in older versions
    _metadata = None


# ---------------------------------------------------------------------------
# BashTool
# ---------------------------------------------------------------------------


class BashTool:
    """Shell command execution with built-in safety validation."""

    @staticmethod
    def execute(
        command: str,
        timeout: int = 120,
        cwd: str | None = None,
    ) -> dict:
        """Execute a shell command and return its output.

        The command is first validated against a built-in deny list of
        known-dangerous patterns.  If the command passes validation it is
        executed via ``subprocess.run`` with ``shell=True``.

        Args:
            command: The shell command to execute.
            timeout: Maximum wall-clock seconds before the process is
                killed.  Defaults to 120.
            cwd: Working directory for the command.  If ``None``, the
                current process working directory is used.

        Returns:
            A dict with keys:

            - ``stdout`` (str): captured standard output (truncated at 64 KB).
            - ``stderr`` (str): captured standard error (truncated at 64 KB).
            - ``exit_code`` (int): process exit code, or ``-1`` on timeout.
            - ``timed_out`` (bool): whether the process was killed due to
              timeout.

        Raises:
            ValueError: If the command matches a dangerous pattern.
            FileNotFoundError: If *cwd* is specified but does not exist.
        """
        # Validate safety
        _validate_command(command)

        # Validate cwd
        if cwd is not None:
            cwd_path = Path(cwd)
            if not cwd_path.is_dir():
                raise FileNotFoundError(f"Working directory does not exist: {cwd}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            return {
                "stdout": _truncate(result.stdout),
                "stderr": _truncate(result.stderr),
                "exit_code": result.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout
            stderr = exc.stderr
            return {
                "stdout": _truncate(stdout if isinstance(stdout, str) else ""),
                "stderr": _truncate(stderr if isinstance(stderr, str) else ""),
                "exit_code": -1,
                "timed_out": True,
            }
