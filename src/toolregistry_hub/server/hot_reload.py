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

A source whose registration raises is logged and left unapplied.  Its old
tools are not re-adopted as current and its new declaration is not recorded
as the applied state, so the next poll that sees a change retries it.  The
Hub's built-in metadata defaults run before the file's ``tool_metadata`` on
reload as well as at startup, so a file override keeps winning.

A malformed file never reaches the registry: :func:`load_config` validates
the whole document before :func:`reload_registry` mutates anything.

Scope note: this is per-process.  Three services sharing one config file
each run their own watcher and converge on the same file; there is no
cross-process coordination, and a reload is not atomic across sources (each
register/unregister/disable is a single registry operation, the same
granularity the admin API uses).

Known limitation: a ``tool_metadata`` entry removed from the file keeps the
value it set until the process restarts.  The same seven fields (``title``,
``defer``, ``search_hint`` and the execution hints) are also writable from
the admin panel, so a reload cannot tell a value the file applied from a
value an operator changed afterwards; restoring the registered value blindly
would discard the newer panel edit.  Adding or changing an entry takes effect
on reload, and the panel can reset a field immediately.  A precise rollback
needs per-field provenance, which is a larger change than this feature.
"""

from __future__ import annotations

import dataclasses
import os
import re
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from toolregistry.config import MCPSource, OpenAPISource, PythonSource
from toolregistry_server import (
    PROFILE_DISABLE_REASON,
    PROFILE_DISABLE_TAGS,
    load_config,
    register_mcp_source,
    register_openapi_source,
    register_python_source,
)

# ``_should_load_source`` is the same predicate ``apply_config`` uses to
# decide whether a source is in scope for the configured mode.  Reusing it
# keeps the reload path from drifting away from the startup path.  The
# namespace-tag helpers are reused for the same reason: a single-source
# reload must tag its tools exactly like the startup path does.
from toolregistry_server.registry_builder import (
    _apply_ns_tags,
    _build_ns_tags,
    _should_load_source,
)

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
            with an empty set when its source is listed but excluded, or when
            its registration failed.
        applied_sources: The declaration last applied successfully per source
            key.  A failed registration is not recorded here, so the next
            reload sees the declaration as changed and retries it.
        profile: Deployment profile applied at startup, if any.  Newly
            registered tools are filtered with the same tag rule after a
            reload; tools that were already registered keep their state.
    """

    config_path: str | None = None
    config: ToolConfig | None = None
    source_tools: dict[SourceKey, frozenset[str]] = field(default_factory=dict)
    applied_sources: dict[SourceKey, ToolSource] = field(default_factory=dict)
    profile: str | None = None


#: ``scheme://user:password@`` in a URL, inside arbitrary text.
_URL_USERINFO = re.compile(r"\b([A-Za-z][A-Za-z0-9+.\-]*://)[^/\s]+@")


def _redact_url_userinfo(text: str) -> str:
    """Remove ``user:password@`` userinfo from a URL in *text*."""
    return _URL_USERINFO.sub(r"\1", text)


def _describe_source(source: ToolSource) -> str:
    """Return a log-safe description of *source*.

    MCP sources keep credentials in ``env``/``auth``, a URL can carry
    userinfo, and stdio arguments can contain tokens.  Only the identifying,
    non-secret part is logged.
    """
    url = getattr(source, "url", None)
    command = getattr(source, "command", None)
    return (
        getattr(source, "class_path", None)
        or getattr(source, "module_path", None)
        or (_redact_url_userinfo(url) if url else None)
        or (f"{command[0]} ..." if command else None)
        or type(source).__name__
    )


def _apply_source(
    registry: ToolRegistry,
    source: ToolSource,
    config: ToolConfig,
) -> frozenset[str]:
    """Register one source and return the names it added.

    The same predicates and per-source registration functions that
    ``apply_config`` uses are called directly, so filtering and namespace
    tags match startup.  The difference is that a registration error
    propagates: the reload path must know that the source failed so it can
    retry instead of recording the failure as the applied state.
    ``tool_metadata`` is not applied here; the caller applies it once for
    the whole config.

    Raises:
        Exception: Whatever the source registration raised.
    """
    if not source.enabled or not _should_load_source(source, config):
        return frozenset()

    before = set(registry._tools)
    try:
        if isinstance(source, PythonSource):
            register_python_source(registry, source)
        elif isinstance(source, MCPSource):
            register_mcp_source(registry, source)
        elif isinstance(source, OpenAPISource):
            register_openapi_source(registry, source)
        else:  # pragma: no cover - the loader only builds the three above
            raise TypeError(f"Unsupported tool source: {type(source).__name__}")

        ns_tags = _build_ns_tags(dataclasses.replace(config, tools=(source,)))
        if ns_tags:
            _apply_ns_tags(registry, ns_tags)
    except Exception:
        # Registration is per tool, so a failure can leave the tools that
        # were already registered.  The caller records an empty name set for
        # a failed source, which would make those tools invisible to the
        # diff: a later removal or edit would skip them and they would live
        # until restart.  Roll the partial registration back.
        for name in set(registry._tools) - before:
            registry._unregister(name)
        raise
    return frozenset(set(registry._tools) - before)


def apply_config_tracked(
    registry: ToolRegistry,
    config: ToolConfig,
) -> dict[SourceKey, frozenset[str]]:
    """Apply *config* source by source and record the names each one added.

    This is the tracked counterpart of
    :func:`toolregistry_server.apply_config`: same registration, same
    filtering, same error handling, plus the name map the watcher needs.
    A source that fails to register is logged and recorded with an empty set,
    exactly as ``apply_config`` does at startup; the next reload retries it.
    """
    sources = index_sources(config.tools)
    produced: dict[SourceKey, frozenset[str]] = {}
    for key, source in sources.items():
        try:
            produced[key] = _apply_source(registry, source, config)
        except Exception as exc:  # noqa: BLE001 - one bad source must not abort startup
            logger.warning(
                f"Failed to load tools from {_describe_source(source)}: {exc}"
            )
            produced[key] = frozenset()
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


def _apply_profile_to_names(
    registry: ToolRegistry,
    names: Iterable[str],
    profile: str,
) -> None:
    """Disable profile-excluded tools among *names*.

    ``apply_profile`` walks the whole registry and can force-enable or
    force-disable namespaces, so re-running it after a reload would override
    an administrator's manual disable.  A reload only constrains the tools it
    just registered, with the same built-in tag mapping startup uses.

    Args:
        registry: The registry to mutate.
        names: Names registered by the current reload.
        profile: Deployment profile name.
    """
    tags = PROFILE_DISABLE_TAGS.get(profile)
    if not tags:
        return
    for name in names:
        tool = registry._tools.get(name)
        if tool is None or tool.metadata is None:
            continue
        if not registry.is_enabled(name):
            continue
        if tool.metadata.all_tags & set(tags):
            registry.disable(name, PROFILE_DISABLE_REASON)


def _register_into(
    registry: ToolRegistry,
    source: ToolSource,
    config: ToolConfig,
) -> frozenset[str] | None:
    """Register *source*, returning the names it added or ``None`` on failure.

    A failed source is logged and retried on the next reload; the caller
    records an empty name set and leaves the applied state unchanged.
    """
    try:
        return _apply_source(registry, source, config)
    except Exception as exc:  # noqa: BLE001 - retried next reload
        logger.warning(f"Failed to load tools from {_describe_source(source)}: {exc}")
        return None


def _reload_source(
    registry: ToolRegistry,
    key: SourceKey,
    source: ToolSource,
    previous: ToolSource | None,
    names: frozenset[str],
    config: ToolConfig,
    state: ReloadState,
) -> tuple[frozenset[str], frozenset[str], dict[str, int]]:
    """Apply one source from the diff.

    Returns:
        ``(names_now, registered_now, counts)``.  ``registered_now`` is empty
        unless the source was registered in this call.

    Note:
        A failed registration records an empty name set and leaves the
        applied declaration unchanged, so the next reload retries.
    """
    counts = {"registered": 0, "unregistered": 0, "enabled": 0, "disabled": 0}
    # ``apply_config`` skips a per-source ``enabled: false`` and any source
    # outside the configured mode; mirror that decision here.
    included = bool(source.enabled) and _should_load_source(source, config)

    if previous is not None and previous == source:
        if included and not names:
            # The source was skipped at startup because it was out of scope,
            # or its last registration failed.  Now that it is in scope,
            # register it instead of only flipping the enable flag on an
            # empty name set.
            added = _register_into(registry, source, config)
            if added is None:
                return frozenset(), frozenset(), counts
            counts["registered"] += len(added)
            return added, added, counts
        # The declaration did not change, so the registered tools are
        # current.  Only a change in scope can still need an action.
        _set_scope(registry, names, included, counts)
        return names, frozenset(), counts

    # Added or changed: drop what the old declaration produced, then
    # register the new one if it is in scope.
    _remove_names(registry, names, counts)
    if not included:
        state.applied_sources[key] = source
        return frozenset(), frozenset(), counts
    added = _register_into(registry, source, config)
    if added is None:
        # Do not record the declaration: ``previous`` stays the last applied
        # one, so the next reload retries.  The old tools were removed
        # above, so the registry reports the source as absent until a retry
        # succeeds.
        return frozenset(), frozenset(), counts
    state.applied_sources[key] = source
    counts["registered"] += len(added)
    return added, added, counts


def reload_registry(
    registry: ToolRegistry,
    state: ReloadState,
    config: ToolConfig,
    *,
    on_reload: Callable[[ToolRegistry], None] | None = None,
) -> dict[str, int]:
    """Apply the difference between the applied state and *config*.

    Args:
        registry: The live registry to mutate.
        state: Tracking state from the previous apply.  Updated in place.
        config: The newly loaded configuration.
        on_reload: Optional callback for metadata defaults that must run
            before the file's ``tool_metadata``.  The Hub passes its
            built-in overrides here, which keeps the reload order identical
            to the startup order, so the file still wins.

    Returns:
        Counts of registered, unregistered, enabled and disabled tools.
    """
    counts = {"registered": 0, "unregistered": 0, "enabled": 0, "disabled": 0}

    # ``applied_sources`` is authoritative.  ``state.config`` is a fallback
    # for a state built before this field existed.
    if not state.applied_sources and state.config is not None:
        state.applied_sources = index_sources(state.config.tools)
    old_sources = dict(state.applied_sources)
    new_sources = index_sources(config.tools)
    produced = dict(state.source_tools)
    # Names registered by this diff; the profile filter touches only these.
    new_names: set[str] = set()

    # Sources no longer declared: their tools leave the registry.
    for key in set(old_sources) - set(new_sources):
        _remove_names(registry, produced.pop(key, frozenset()), counts)
        state.applied_sources.pop(key, None)

    for key, source in new_sources.items():
        names, registered, delta = _reload_source(
            registry,
            key,
            source,
            old_sources.get(key),
            produced.get(key, frozenset()),
            config,
            state,
        )
        produced[key] = names
        new_names.update(registered)
        for name, value in delta.items():
            counts[name] += value

    # Hub-built-in metadata defaults run first; the file's overrides run
    # afterwards, matching ``build_registry``.
    if on_reload is not None:
        on_reload(registry)

    # Tools registered by this diff must obey the deployment profile that
    # was applied to the startup registry.  Run this after the metadata
    # callback, which supplies the Hub's namespace tags.
    if state.profile and new_names:
        _apply_profile_to_names(registry, new_names, state.profile)

    # Per-tool metadata overrides, matching what ``apply_config`` does at
    # startup.  Removing an entry from the file does not revert the registry:
    # the same fields are writable from the admin panel, so a rollback would
    # need per-field provenance (see the module docstring).
    if config.tool_metadata:
        registry.apply_metadata_config(config.tool_metadata)

    state.config = config
    state.source_tools = produced
    return counts


def reload_from_path(
    registry: ToolRegistry,
    state: ReloadState,
    path: str | None = None,
    *,
    on_reload: Callable[[ToolRegistry], None] | None = None,
) -> bool:
    """Re-read the config file and apply it.

    Args:
        registry: The live registry to mutate.
        state: Tracking state from the previous apply.
        path: Config path; defaults to :attr:`ReloadState.config_path`.
        on_reload: Optional metadata-defaults callback, passed through to
            :func:`reload_registry`.

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

    counts = reload_registry(registry, state, config, on_reload=on_reload)
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
        # A reload mutates the shared registry, so serialise polls: two
        # callers (the thread plus a test or a manual trigger) must not
        # interleave two diffs.
        self._reload_lock = threading.Lock()
        # Start from a sentinel, not from the stat at construction: the
        # registry was built before this object existed, so an edit in that
        # window would otherwise be adopted as the baseline and never
        # reloaded.  The first poll therefore always runs; the diff is
        # idempotent, so an unchanged file produces no work.
        self._last_seen: tuple[int, int] | None = (0, 0)

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
        if current is None:
            return False
        with self._reload_lock:
            if current == self._last_seen:
                return False
            # Remember the observed state before reloading: a parse failure
            # must not retry until the file changes again.
            self._last_seen = current
            # The metadata defaults callback runs inside the reload, before
            # the file's tool_metadata, so the file keeps winning.
            return reload_from_path(
                self.registry,
                self.state,
                on_reload=self.on_reload,
            )

    def run(self) -> None:
        while not self._stop_event.wait(self.interval):
            try:
                self.poll_once()
            except Exception as exc:  # noqa: BLE001 - a reload bug must not kill the watcher
                logger.warning(f"Config reload failed; watcher continues: {exc}")

    def stop(self, timeout: float | None = None) -> None:
        """Ask the thread to exit.

        Args:
            timeout: When given, wait this many seconds for the thread to
                finish.  ``None`` returns immediately.
        """
        self._stop_event.set()
        if timeout is not None and self.is_alive():
            self.join(timeout)
