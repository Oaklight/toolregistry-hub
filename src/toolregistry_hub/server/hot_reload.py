"""Hot reload of ``tools.jsonc`` for a running Hub process.

The Hub builds its registry once at startup.  With ``--config-reload`` the
process also starts :class:`ConfigWatcher`, a daemon thread that polls the
config file's ``mtime``/size and applies a source-level diff to the live
registry:

- a source added to the file is registered;
- a source removed from the file is unregistered;
- a source that is still listed but now excluded (``enabled: false`` or
  filtered out by ``mode``/``disabled``/``enabled``) is disabled, and its
  tools are re-enabled when the source becomes included again;
- a source whose declaration changed is unregistered and registered again.

The diff works on *sources*, not on the whole config, so an unrelated edit
does not re-import every tool or reconnect every MCP server.

A malformed file never reaches the registry: :func:`load_config` validates
the whole document before :func:`reload_registry` mutates anything.

Scope note: this is per-process.  Three services sharing one config file
each run their own watcher and converge on the same file; there is no
cross-process coordination, and a reload is not atomic across sources (each
register/unregister/disable is a single registry operation, the same
granularity the admin API uses).
"""

from __future__ import annotations

import dataclasses
import os
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from toolregistry_server import apply_config, load_config

# ``_should_load_source`` is the same predicate ``apply_config`` uses to
# decide whether a source is in scope for the configured mode.  Reusing it
# keeps the reload path from drifting away from the startup path.
from toolregistry_server.registry_builder import _should_load_source

from .._vendor.structlog import get_logger

if TYPE_CHECKING:
    from toolregistry import ToolRegistry
    from toolregistry.config import ToolConfig, ToolSource

logger = get_logger()

#: Reason recorded on tools disabled because their source left the scope of
#: the config.  Only tools carrying this reason are re-enabled by a reload;
#: tools disabled for another reason (missing API key, admin panel) stay off.
CONFIG_DISABLE_REASON = "Disabled by config (hot reload)"

#: A source is identified by its declaration, not by its position, so
#: reordering the ``tools`` list is not treated as a change.  Fields that
#: live in unhashable containers (``kwargs``, ``env``, ``auth``) are not part
#: of the key; a change to them is still detected by comparing the full
#: source objects once the keys match.
SourceKey = tuple[Any, ...]


def source_key(source: ToolSource) -> SourceKey:
    """Return the stable identity of a tool source declaration."""
    return (
        type(source).__name__,
        getattr(source, "namespace", None),
        getattr(source, "class_path", None),
        getattr(source, "module_path", None),
        getattr(source, "url", None),
        getattr(source, "command", None),
    )


def index_sources(sources: Iterable[ToolSource]) -> dict[SourceKey, ToolSource]:
    """Map each source declaration to its key.

    Two sources may share a key (for example, the same OpenAPI URL twice
    with different auth).  The occurrence index is appended so both survive
    indexing; the order inside the file decides which is which.
    """
    seen: dict[SourceKey, int] = {}
    indexed: dict[SourceKey, ToolSource] = {}
    for source in sources:
        base = source_key(source)
        occurrence = seen.get(base, 0)
        seen[base] = occurrence + 1
        key: SourceKey = base if occurrence == 0 else (*base, occurrence)
        indexed[key] = source
    return indexed


@dataclass
class ReloadState:
    """What the watcher needs to diff an edited config against the registry.

    Attributes:
        config_path: Resolved config file path, or ``None`` when the Hub is
            running on its built-in defaults (nothing to watch).
        config: The configuration the registry currently reflects.
        source_tools: Registered tool names per source key.  A key is present
            with an empty set when its source is listed but excluded.
    """

    config_path: str | None = None
    config: ToolConfig | None = None
    source_tools: dict[SourceKey, frozenset[str]] = field(default_factory=dict)


def _apply_source(
    registry: ToolRegistry,
    source: ToolSource,
    config: ToolConfig,
) -> frozenset[str]:
    """Register one source and return the names it added.

    ``apply_config`` is reused with a single-source config so the include
    filter, namespace tags and per-source error handling match startup
    exactly.  ``tool_metadata`` is stripped: it is applied once for the whole
    config by the caller.
    """
    before = set(registry._tools)
    single = dataclasses.replace(config, tools=(source,), tool_metadata={})
    apply_config(registry, single)
    return frozenset(set(registry._tools) - before)


def apply_config_tracked(
    registry: ToolRegistry,
    config: ToolConfig,
) -> dict[SourceKey, frozenset[str]]:
    """Apply *config* source by source and record the names each one added.

    This is the tracked counterpart of
    :func:`toolregistry_server.apply_config`: same registration, same
    filtering, same error handling, plus the name map the watcher needs.
    """
    sources = index_sources(config.tools)
    produced: dict[SourceKey, frozenset[str]] = {}
    for key, source in sources.items():
        produced[key] = _apply_source(registry, source, config)
    return produced


def _remove_names(
    registry: ToolRegistry, names: Iterable[str], counts: dict[str, int]
) -> None:
    """Unregister *names*, counting the ones that were actually present."""
    for name in names:
        if registry._unregister(name):
            counts["unregistered"] += 1


def _set_scope(
    registry: ToolRegistry,
    names: Iterable[str],
    included: bool,
    counts: dict[str, int],
) -> None:
    """Enable or disable *names* for a source whose declaration is unchanged.

    Only tools disabled by this module are re-enabled, so a tool turned off
    for a missing API key or from the admin panel stays off.
    """
    for name in names:
        if included:
            if registry.get_disable_reason(name) == CONFIG_DISABLE_REASON:
                registry.enable(name)
                counts["enabled"] += 1
        elif registry.is_enabled(name):
            registry.disable(name, CONFIG_DISABLE_REASON)
            counts["disabled"] += 1


def reload_registry(
    registry: ToolRegistry,
    state: ReloadState,
    config: ToolConfig,
) -> dict[str, int]:
    """Apply the difference between :attr:`ReloadState.config` and *config*.

    Args:
        registry: The live registry to mutate.
        state: Tracking state from the previous apply.  Updated in place.
        config: The newly loaded configuration.

    Returns:
        Counts of registered, unregistered, enabled and disabled tools.
    """
    counts = {"registered": 0, "unregistered": 0, "enabled": 0, "disabled": 0}

    old_sources = index_sources(state.config.tools) if state.config else {}
    new_sources = index_sources(config.tools)
    produced = dict(state.source_tools)

    # Sources no longer declared: their tools leave the registry.
    for key in set(old_sources) - set(new_sources):
        _remove_names(registry, produced.pop(key, frozenset()), counts)

    for key, source in new_sources.items():
        names = produced.get(key, frozenset())
        previous = old_sources.get(key)
        # ``apply_config`` skips a per-source ``enabled: false`` and any
        # source outside the configured mode; mirror that decision here.
        included = bool(source.enabled) and _should_load_source(source, config)

        if previous is not None and previous == source:
            # The declaration did not change, so the registered tools are
            # current.  Only a change in scope can still need an action.
            _set_scope(registry, names, included, counts)
            continue

        # Added or changed: drop what the old declaration produced, then
        # register the new one if it is in scope.
        _remove_names(registry, names, counts)
        produced[key] = (
            _apply_source(registry, source, config) if included else frozenset()
        )
        counts["registered"] += len(produced[key])

    # Per-tool metadata overrides, matching what ``apply_config`` does at
    # startup.  Removing an entry from the file does not revert the registry
    # to the registered value; that would need a stored baseline and is out
    # of scope for #144.
    if config.tool_metadata:
        registry.apply_metadata_config(config.tool_metadata)

    state.config = config
    state.source_tools = produced
    return counts


def reload_from_path(
    registry: ToolRegistry,
    state: ReloadState,
    path: str | None = None,
) -> bool:
    """Re-read the config file and apply it.

    Returns:
        ``True`` when the file parsed and the diff was applied.  ``False``
        when it could not be read or parsed; the registry is untouched in
        that case.
    """
    target = path or state.config_path
    if not target:
        return False
    try:
        config = load_config(target)
    except Exception as exc:  # noqa: BLE001 - a bad edit must not kill the watcher
        logger.warning(f"Config reload skipped; keeping the current registry: {exc}")
        return False

    counts = reload_registry(registry, state, config)
    logger.info(
        "Config reloaded from "
        f"{target}: {counts['registered']} registered, "
        f"{counts['unregistered']} unregistered, "
        f"{counts['enabled']} enabled, {counts['disabled']} disabled"
    )
    return True


class ConfigWatcher(threading.Thread):
    """Daemon thread that polls the config file and reloads it on change.

    Args:
        registry: Live registry to update.
        state: Tracking state produced by
            :func:`apply_config_tracked` during startup.
        interval: Seconds between polls.
        on_reload: Optional callback run after a successful reload, used to
            re-apply Hub metadata overrides to newly registered tools.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        state: ReloadState,
        *,
        interval: float = 2.0,
        on_reload: Callable[[ToolRegistry], None] | None = None,
    ) -> None:
        super().__init__(name="toolregistry-hub-config-reload", daemon=True)
        self.registry = registry
        self.state = state
        self.interval = interval
        self.on_reload = on_reload
        self._stop_event = threading.Event()
        self._last_seen = self._stat_key()

    def _stat_key(self) -> tuple[int, int] | None:
        """Return ``(mtime_ns, size)``, or ``None`` when the file is absent.

        A missing file is not an error: editors that write through a
        temporary file and rename leave the path absent for a moment.
        """
        if not self.state.config_path:
            return None
        try:
            info = os.stat(self.state.config_path)
        except OSError:
            return None
        return (info.st_mtime_ns, info.st_size)

    def poll_once(self) -> bool:
        """Reload if the file changed since the last poll.

        Returns:
            ``True`` when a reload was applied.
        """
        current = self._stat_key()
        if current is None or current == self._last_seen:
            return False
        # Remember the observed state before reloading: a parse failure must
        # not retry until the file changes again.
        self._last_seen = current
        applied = reload_from_path(self.registry, self.state)
        if applied and self.on_reload is not None:
            self.on_reload(self.registry)
        return applied

    def run(self) -> None:
        while not self._stop_event.wait(self.interval):
            self.poll_once()

    def stop(self) -> None:
        """Ask the thread to exit; returns immediately."""
        self._stop_event.set()
