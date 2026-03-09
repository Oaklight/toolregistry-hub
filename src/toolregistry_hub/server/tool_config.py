"""Startup tool configuration via JSONC files.

Provides a declarative way to control which tool namespaces are enabled or
disabled when the server starts.  The configuration file uses JSONC format
(JSON with ``//`` and ``/* */`` comments), parsed with zero external
dependencies via a lightweight regex preprocessor.

Discovery order:
    1. Explicit *config_path* argument (from CLI ``--tools-config``)
    2. ``TOOLS_CONFIG`` environment variable
    3. ``./tools.jsonc`` in the current working directory
    4. No file found → ``None`` (all tools enabled, backward compatible)

Priority model::

    Config file  >  Configurable auto-disable  >  Default (all enabled)
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


from loguru import logger
from toolregistry import ToolRegistry


# ---------------------------------------------------------------------------
# JSONC preprocessor
# ---------------------------------------------------------------------------

# Matches: double-quoted strings | // line comments | /* block comments */
_JSONC_RE = re.compile(
    r'"(?:[^"\\]|\\.)*"'  # double-quoted string (group 0 implicit)
    r"|//[^\n]*"  # single-line comment
    r"|/\*.*?\*/",  # block comment (non-greedy)
    re.DOTALL,
)


def _strip_json_comments(text: str) -> str:
    """Remove ``//`` and ``/* */`` comments from JSONC text.

    Preserves comment-like content inside double-quoted strings.

    Args:
        text: Raw JSONC text.

    Returns:
        Clean JSON text suitable for ``json.loads()``.
    """

    def _replacer(match: re.Match) -> str:
        s = match.group(0)
        if s.startswith('"'):
            return s  # preserve strings
        return ""  # strip comments

    return _JSONC_RE.sub(_replacer, text)


# ---------------------------------------------------------------------------
# ToolConfig dataclass
# ---------------------------------------------------------------------------


@dataclass
class ToolEntry:
    """A tool entry from the configuration file.

    Attributes:
        class_path: Fully qualified class path,
            e.g. ``"toolregistry_hub.calculator.Calculator"``.
        namespace: Namespace for the tool,
            e.g. ``"calculator"`` or ``"web/brave_search"``.
    """

    class_path: str
    namespace: str


@dataclass
class ToolConfig:
    """Parsed startup tool configuration.

    Attributes:
        mode: Either ``"denylist"`` (disable listed namespaces) or
            ``"allowlist"`` (enable only listed namespaces).
        disabled: Namespaces to disable (used in denylist mode).
        enabled: Namespaces to enable (used in allowlist mode).
        tools: Optional list of tool entries from the configuration file.
            If ``None``, the built-in default tool list is used.
        source: Path of the configuration file that was loaded.
    """

    mode: str = "denylist"
    disabled: List[str] = field(default_factory=list)
    enabled: List[str] = field(default_factory=list)
    tools: Optional[List[ToolEntry]] = None
    source: str = ""


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def load_tool_config(config_path: Optional[str] = None) -> Optional[ToolConfig]:
    """Discover and parse a JSONC tool configuration file.

    Args:
        config_path: Explicit path to the config file.  If ``None``, the
            discovery order described in the module docstring is used.

    Returns:
        A :class:`ToolConfig` instance, or ``None`` if no config file was
        found (backward-compatible default).

    Raises:
        ValueError: If the config file exists but contains invalid JSON or
            has an unrecognised ``mode`` value.
        FileNotFoundError: If *config_path* is given explicitly but does not
            exist.
    """
    path = _resolve_config_path(config_path)
    if path is None:
        return None

    text = path.read_text(encoding="utf-8")
    clean = _strip_json_comments(text)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Config file {path} must contain a JSON object, got {type(data).__name__}"
        )

    mode = data.get("mode", "denylist")
    if mode not in ("denylist", "allowlist"):
        raise ValueError(
            f"Invalid mode '{mode}' in {path}. Must be 'denylist' or 'allowlist'."
        )

    disabled = data.get("disabled", [])
    enabled = data.get("enabled", [])

    if not isinstance(disabled, list) or not all(isinstance(x, str) for x in disabled):
        raise ValueError(f"'disabled' in {path} must be a list of strings.")

    if not isinstance(enabled, list) or not all(isinstance(x, str) for x in enabled):
        raise ValueError(f"'enabled' in {path} must be a list of strings.")

    # Parse optional 'tools' field
    tools_list = data.get("tools")
    tools = None
    if tools_list is not None:
        if not isinstance(tools_list, list):
            logger.warning(
                f"Invalid 'tools' field in {path}: "
                f"expected list, got {type(tools_list).__name__}"
            )
        else:
            tools = []
            for i, entry in enumerate(tools_list):
                if not isinstance(entry, dict):
                    logger.warning(
                        f"Invalid tool entry at index {i} in {path}: expected dict"
                    )
                    continue
                class_path = entry.get("class")
                namespace = entry.get("namespace")
                if not class_path or not namespace:
                    logger.warning(
                        f"Tool entry at index {i} missing 'class' or "
                        f"'namespace' in {path}"
                    )
                    continue
                tools.append(ToolEntry(class_path=class_path, namespace=namespace))

    return ToolConfig(
        mode=mode,
        disabled=disabled,
        enabled=enabled,
        tools=tools,
        source=str(path),
    )


def _resolve_config_path(config_path: Optional[str]) -> Optional[Path]:
    """Resolve the configuration file path using the discovery order.

    Args:
        config_path: Explicit path from CLI argument.

    Returns:
        Resolved :class:`Path`, or ``None`` if no config file was found.

    Raises:
        FileNotFoundError: If *config_path* is given but does not exist.
    """
    # 1. Explicit CLI argument
    if config_path is not None:
        p = Path(config_path)
        if not p.is_file():
            raise FileNotFoundError(f"Tools config file not found: {config_path}")
        return p

    # 2. Environment variable
    env_path = os.environ.get("TOOLS_CONFIG")
    if env_path:
        p = Path(env_path)
        try:
            if p.is_file():
                return p
        except PermissionError:
            logger.warning(
                f"TOOLS_CONFIG={env_path} exists but is not accessible "
                f"(permission denied), ignoring."
            )
            return None
        logger.warning(f"TOOLS_CONFIG={env_path} does not exist, ignoring.")

    # 3. Working directory default
    default = Path("tools.jsonc")
    try:
        if default.is_file():
            return default
    except PermissionError:
        logger.warning(
            f"Found {default} but cannot access it (permission denied). "
            f"Ensure the file and its parent directory are readable by the "
            f"current user (e.g. chmod 755 on the directory, chmod 644 on "
            f"the file). Skipping tool config."
        )
        return None

    # 4. No config found
    return None


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_tool_config(registry: ToolRegistry, config: ToolConfig) -> None:
    """Apply a :class:`ToolConfig` to a :class:`ToolRegistry`.

    In **denylist** mode, every namespace listed in ``config.disabled`` is
    disabled.  In **allowlist** mode, every namespace *not* listed in
    ``config.enabled`` is disabled.

    Args:
        registry: The registry to modify.
        config: The parsed tool configuration.
    """
    # Collect all known namespaces from the registry
    namespaces = {
        tool.namespace
        for tool in registry._tools.values()
        if tool.namespace is not None
    }

    if config.mode == "denylist":
        _apply_denylist(registry, config.disabled, namespaces)
    else:
        _apply_allowlist(registry, config.enabled, namespaces)

    logger.info(f"Applied tool config from {config.source} (mode={config.mode})")


def _ns_matches(tool_namespace: str, pattern: str) -> bool:
    """Check if a tool namespace matches a config pattern.

    Supports exact match and prefix match for hierarchical namespaces.
    For example, pattern ``"web"`` matches ``"web/brave_search"``.

    Args:
        tool_namespace: The tool's namespace (e.g. ``"web/brave_search"``).
        pattern: The config pattern (e.g. ``"web"`` or ``"web/brave_search"``).

    Returns:
        True if the namespace matches the pattern.
    """
    return tool_namespace == pattern or tool_namespace.startswith(pattern + "/")


def _apply_denylist(
    registry: ToolRegistry,
    disabled_namespaces: List[str],
    known_namespaces: set,
) -> None:
    """Disable tools belonging to the listed namespaces.

    Supports hierarchical namespace matching: ``"web"`` disables all
    ``web/*`` namespaces.
    """
    for ns in disabled_namespaces:
        matched = any(_ns_matches(known, ns) for known in known_namespaces)
        if not matched:
            logger.warning(f"Config denylist: unknown namespace '{ns}', skipping.")
            continue
        for tool_name, tool in registry._tools.items():
            if tool.namespace and _ns_matches(tool.namespace, ns):
                registry.disable(tool_name, reason="Disabled by config file")
        logger.info(f"Config denylist: disabled namespace '{ns}'")


def _apply_allowlist(
    registry: ToolRegistry,
    enabled_namespaces: List[str],
    known_namespaces: set,
) -> None:
    """Disable tools whose namespace is NOT in the allow list.

    Supports hierarchical namespace matching: ``"web"`` allows all
    ``web/*`` namespaces.
    """
    # Warn about unknown namespaces in the allow list
    for ns in enabled_namespaces:
        matched = any(_ns_matches(known, ns) for known in known_namespaces)
        if not matched:
            logger.warning(f"Config allowlist: unknown namespace '{ns}', skipping.")

    for tool_name, tool in registry._tools.items():
        if tool.namespace is not None and not any(
            _ns_matches(tool.namespace, ns) for ns in enabled_namespaces
        ):
            registry.disable(tool_name, reason="Not in allowlist")
            logger.debug(
                f"Config allowlist: disabled '{tool_name}' (namespace '{tool.namespace}')"
            )
