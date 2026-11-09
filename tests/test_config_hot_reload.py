"""Tests for tools.jsonc hot reload (#144).

The watcher is opt-in and must never corrupt a running registry: a bad edit
is ignored, a good edit is applied source by source.
"""

from __future__ import annotations

import time

import pytest
from toolregistry.config import MCPSource
from toolregistry.tool import ToolTag
from toolregistry_server import PROFILE_DISABLE_REASON, apply_profile, load_config

from toolregistry_hub.server.hot_reload import (
    CONFIG_DISABLE_REASON,
    ConfigWatcher,
    ReloadState,
    SourceStatus,
    _describe_source,
    apply_config_tracked,
    reload_from_path,
    reload_registry,
    source_key,
)
from toolregistry_hub.server.registry import apply_hub_overrides, build_registry


def _write_config(path, body: str) -> None:
    """Write a JSONC config, keeping the syntax obvious in each test."""
    path.write_text("{\n" + body + "\n}\n", encoding="utf-8")


def _sources(*entries: str) -> str:
    return '"tools": [' + ", ".join(entries) + "]"


CALCULATOR = (
    '{"class": "toolregistry_hub.calculator.Calculator", "namespace": "calculator"}'
)
DATETIME = (
    '{"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "datetime"}'
)
UNIT = '{"class": "toolregistry_hub.unit_converter.UnitConverter", "namespace": "unit_converter"}'
# A namespace outside the Hub's built-in namespaces, so a source-declared
# tag survives the tool declarations and the profile filter can see it.
DT2 = (
    '{"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "dt2", '
    '"tags": ["file_system"]}'
)
DT2_V2 = (
    '{"class": "toolregistry_hub.datetime_utils.DateTime", "namespace": "dt2", '
    '"tags": ["file_system", "read_only"]}'
)


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "tools.jsonc"
    _write_config(path, _sources(CALCULATOR, DATETIME))
    return path


@pytest.fixture
def tracked(config_path):
    """A registry built with tracking enabled, plus its reload state."""
    state = ReloadState()
    registry = build_registry(
        tools_config_path=str(config_path),
        enable_discovery=False,
        reload_state=state,
    )
    return registry, state


class TestTrackedBuild:
    def test_records_one_entry_per_source(self, tracked):
        registry, state = tracked

        assert len(state.config_path) > 0
        assert len(state.source_tools) == 2
        # Every source produced at least one tool, and the names exist.
        produced = set().union(*state.source_tools.values())
        assert produced
        assert produced <= set(registry._tools)

    def test_tracked_build_matches_untracked(self, config_path):
        tracked_registry = build_registry(
            tools_config_path=str(config_path),
            enable_discovery=False,
            reload_state=ReloadState(),
        )
        plain_registry = build_registry(
            tools_config_path=str(config_path),
            enable_discovery=False,
        )

        assert set(tracked_registry._tools) == set(plain_registry._tools)

    def test_apply_config_tracked_returns_name_sets(self, config_path):
        from toolregistry import ToolRegistry

        registry = ToolRegistry(name="tracked-test")
        names = apply_config_tracked(registry, load_config(str(config_path)))

        assert len(names) == 2
        assert (
            "calculator-evaluate"
            in names[next(k for k in names if k[1] == "calculator")]
        )


class TestReloadDiff:
    def test_added_source_is_registered(self, tracked, config_path):
        registry, state = tracked
        assert "unit_converter-convert" not in registry._tools

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        counts = reload_registry(registry, state, load_config(str(config_path)))

        assert "unit_converter-convert" in registry._tools
        assert counts["registered"] >= 1

    def test_removed_source_is_unregistered(self, tracked, config_path):
        registry, state = tracked
        assert "datetime-now" in registry._tools

        _write_config(config_path, _sources(CALCULATOR))
        reload_registry(registry, state, load_config(str(config_path)))

        assert "datetime-now" not in registry._tools
        assert "calculator-evaluate" in registry._tools

    def test_scope_change_disables_and_reenables(self, tracked, config_path):
        registry, state = tracked

        _write_config(
            config_path,
            '"mode": "allowlist", "enabled": ["calculator"], '
            + _sources(CALCULATOR, DATETIME),
        )
        counts = reload_registry(registry, state, load_config(str(config_path)))

        # The tool stays registered so callers holding a reference still
        # resolve a name, but it is not served.
        assert "datetime-now" in registry._tools
        assert registry.is_enabled("datetime-now") is False
        assert registry.get_disable_reason("datetime-now") == CONFIG_DISABLE_REASON
        assert counts["disabled"] >= 1

        _write_config(config_path, _sources(CALCULATOR, DATETIME))
        reload_registry(registry, state, load_config(str(config_path)))

        assert registry.is_enabled("datetime-now") is True

    def test_changed_source_is_replaced(self, tracked, config_path):
        registry, state = tracked
        old_tool = registry._tools["calculator-evaluate"]

        # A different namespace produces a different name for the same code.
        _write_config(
            config_path,
            _sources(
                '{"class": "toolregistry_hub.calculator.Calculator", "namespace": "math"}',
                DATETIME,
            ),
        )
        reload_registry(registry, state, load_config(str(config_path)))

        assert "calculator-evaluate" not in registry._tools
        assert "math-evaluate" in registry._tools
        assert registry._tools["math-evaluate"] is not old_tool

    def test_unrelated_edit_does_not_touch_registry(self, tracked, config_path):
        registry, state = tracked
        before = dict(registry._tools)

        _write_config(
            config_path,
            '"mode": "denylist", "disabled": [], ' + _sources(CALCULATOR, DATETIME),
        )
        counts = reload_registry(registry, state, load_config(str(config_path)))

        assert counts == {
            "registered": 0,
            "unregistered": 0,
            "enabled": 0,
            "disabled": 0,
        }
        assert registry._tools == before


class TestMetadataOrder:
    def test_file_override_survives_a_reload(self, tmp_path):
        """The file's tool_metadata must win over the Hub defaults, as at startup."""
        path = tmp_path / "tools.jsonc"
        metadata = '"tool_metadata": {"calculator-evaluate": {"defer": false}}, '
        _write_config(path, metadata + _sources(CALCULATOR, DATETIME))

        state = ReloadState()
        registry = build_registry(
            tools_config_path=str(path),
            enable_discovery=False,
            reload_state=state,
        )
        assert registry._tools["calculator-evaluate"].metadata.defer is False

        _write_config(path, metadata + _sources(CALCULATOR, DATETIME, UNIT))
        reload_registry(
            registry,
            state,
            load_config(str(path)),
            on_reload=apply_hub_overrides,
        )

        # Hub defaults set defer=True for the calculator namespace; the file
        # overrides it to False and must still win after the reload.
        assert registry._tools["calculator-evaluate"].metadata.defer is False


class TestOverrideScope:
    """Hub defaults apply only to the tools a reload registered."""

    def test_panel_edit_survives_an_unrelated_reload(self, tracked, config_path):
        registry, state = tracked
        assert registry._tools["calculator-evaluate"].metadata.defer is True

        # What the admin panel does: change two fields the Hub also defaults.
        registry.update_tool_metadata(
            "calculator-evaluate",
            defer=False,
            tags={ToolTag.DESTRUCTIVE},
        )

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        reload_registry(
            registry,
            state,
            load_config(str(config_path)),
            on_reload=apply_hub_overrides,
        )

        edited = registry._tools["calculator-evaluate"].metadata
        assert edited.defer is False
        assert edited.tags == {ToolTag.DESTRUCTIVE}

        # A tool registered by this reload still gets the Hub defaults.
        added = registry._tools["unit_converter-convert"].metadata
        assert added.defer is True
        assert added.tags == {ToolTag.READ_ONLY}

    def test_callback_receives_only_the_registered_names(self, tracked, config_path):
        registry, state = tracked
        seen: list[set[str]] = []

        def record(_registry, names):
            seen.append(set(names))

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        reload_registry(
            registry,
            state,
            load_config(str(config_path)),
            on_reload=record,
        )

        new_names = {
            name for name in registry._tools if name.startswith("unit_converter-")
        }
        assert new_names
        assert seen == [new_names]
        assert "calculator-evaluate" not in seen[0]


class TestScopeTransitions:
    def test_source_excluded_at_startup_registers_when_in_scope(self, tmp_path):
        """A source skipped at startup must register once global rules allow it."""
        path = tmp_path / "tools.jsonc"
        _write_config(
            path,
            '"mode": "allowlist", "enabled": ["calculator"], '
            + _sources(CALCULATOR, DATETIME),
        )
        state = ReloadState()
        registry = build_registry(
            tools_config_path=str(path),
            enable_discovery=False,
            reload_state=state,
        )
        assert "datetime-now" not in registry._tools

        _write_config(path, _sources(CALCULATOR, DATETIME))
        counts = reload_registry(registry, state, load_config(str(path)))

        assert "datetime-now" in registry._tools
        assert counts["registered"] >= 1


class TestFailedRegistration:
    def test_a_failed_source_is_retried_on_the_next_reload(
        self, tracked, config_path, monkeypatch
    ):
        import toolregistry_hub.server.hot_reload as hot_reload

        registry, state = tracked
        real = hot_reload.register_python_source
        attempts = 0

        def flaky(reg, source):
            nonlocal attempts
            if source.namespace == "unit_converter":
                attempts += 1
                if attempts == 1:
                    raise RuntimeError("transient failure")
            return real(reg, source)

        monkeypatch.setattr(hot_reload, "register_python_source", flaky)

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        config = load_config(str(config_path))
        reload_registry(registry, state, config)

        unit_source = next(s for s in config.tools if s.namespace == "unit_converter")
        key = source_key(unit_source)
        assert "unit_converter-convert" not in registry._tools
        # The failed declaration must not be recorded as applied, or the
        # unchanged-declaration branch would never retry it.
        assert key not in state.applied_sources
        assert state.source_tools[key] == frozenset()

        reload_registry(registry, state, load_config(str(config_path)))

        assert "unit_converter-convert" in registry._tools
        assert key in state.applied_sources

    def test_partial_registration_is_rolled_back(
        self, tracked, config_path, monkeypatch
    ):
        """Tools registered before a source fails must not outlive the attempt."""
        import toolregistry_hub.server.hot_reload as hot_reload

        registry, state = tracked
        real = hot_reload.register_python_source

        def partial_then_raise(reg, source):
            if source.namespace == "unit_converter":
                # Simulate a source that registers some tools, then fails.
                real(reg, source)
                raise RuntimeError("failed after a partial registration")
            return real(reg, source)

        monkeypatch.setattr(hot_reload, "register_python_source", partial_then_raise)

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        reload_registry(registry, state, load_config(str(config_path)))

        # Without the rollback this tool stays registered but is absent from
        # source_tools, so a later removal or edit would never see it.
        assert "unit_converter-convert" not in registry._tools

        monkeypatch.setattr(hot_reload, "register_python_source", real)
        reload_registry(registry, state, load_config(str(config_path)))
        assert "unit_converter-convert" in registry._tools

        _write_config(config_path, _sources(CALCULATOR, DATETIME))
        reload_registry(registry, state, load_config(str(config_path)))
        assert "unit_converter-convert" not in registry._tools


class TestProfileFilter:
    """A reload must not re-expose a tool the deployment profile excluded."""

    @staticmethod
    def _build(path):
        state = ReloadState()
        registry = build_registry(
            tools_config_path=str(path),
            enable_discovery=False,
            reload_state=state,
        )
        state.profile = "remote"
        apply_profile(registry, "remote")
        return registry, state

    def test_redeclared_source_stays_profile_disabled(self, tmp_path):
        path = tmp_path / "tools.jsonc"
        _write_config(path, _sources(CALCULATOR, DT2))
        registry, state = self._build(path)
        assert registry.get_disable_reason("dt2-now") == PROFILE_DISABLE_REASON

        # An administrator's manual disable must survive the reload.
        registry.disable("calculator-evaluate", "admin edit")

        _write_config(path, _sources(CALCULATOR, DT2_V2))
        reload_registry(
            registry,
            state,
            load_config(str(path)),
            on_reload=apply_hub_overrides,
        )

        # The source was unregistered and registered again; the profile
        # filter must still apply to the new tools.
        assert registry.get_disable_reason("dt2-now") == PROFILE_DISABLE_REASON
        assert registry.get_disable_reason("calculator-evaluate") == "admin edit"

    def test_unrelated_reload_does_not_change_profile_state(self, tmp_path):
        path = tmp_path / "tools.jsonc"
        _write_config(path, _sources(CALCULATOR, DT2))
        registry, state = self._build(path)

        _write_config(path, _sources(CALCULATOR, DT2, UNIT))
        reload_registry(
            registry,
            state,
            load_config(str(path)),
            on_reload=apply_hub_overrides,
        )

        assert "unit_converter-convert" in registry._tools
        assert registry.get_disable_reason("dt2-now") == PROFILE_DISABLE_REASON


class TestDescribeSource:
    def test_url_userinfo_is_redacted(self):
        source = MCPSource(
            transport="streamable-http", url="https://u:secret@example.com/mcp"
        )
        assert _describe_source(source) == "https://example.com/mcp"

    def test_stdio_arguments_are_not_logged(self):
        source = MCPSource(
            transport="stdio", command=("npx", "srv", "--token", "SECRET")
        )
        assert _describe_source(source) == "npx ..."


class TestMalformedConfig:
    def test_invalid_config_leaves_registry_untouched(self, tracked, config_path):
        registry, state = tracked
        before = dict(registry._tools)

        config_path.write_text("{ this is not jsonc", encoding="utf-8")
        applied = reload_from_path(registry, state)

        assert applied is False
        assert registry._tools == before


class TestWatcher:
    def test_reloads_when_the_file_changes(self, tracked, config_path):
        registry, state = tracked
        watcher = ConfigWatcher(registry, state, interval=0.02)
        watcher.start()
        try:
            time.sleep(0.05)
            _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))

            deadline = time.time() + 5
            while time.time() < deadline and "unit_converter-convert" not in (
                registry._tools
            ):
                time.sleep(0.02)

            assert "unit_converter-convert" in registry._tools
        finally:
            watcher.stop()
            watcher.join(timeout=2)
            assert not watcher.is_alive()

    def test_poll_once_is_a_noop_after_the_first_poll(self, tracked):
        registry, state = tracked
        watcher = ConfigWatcher(registry, state, interval=0.02)

        # The first poll always runs: it reconciles the window between the
        # registry build and the watcher start.  The diff is idempotent.
        assert watcher.poll_once() is True
        assert watcher.poll_once() is False

    def test_first_poll_picks_up_an_edit_before_the_watcher_started(
        self, tracked, config_path
    ):
        """An edit made between the registry build and the thread start is not lost."""
        registry, state = tracked

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        watcher = ConfigWatcher(registry, state, interval=0.02)

        assert watcher.poll_once() is True
        assert "unit_converter-convert" in registry._tools

    def test_missing_file_is_not_an_error(self, tracked, config_path):
        registry, state = tracked
        watcher = ConfigWatcher(registry, state, interval=0.02)
        config_path.unlink()

        assert watcher.poll_once() is False

    def test_run_survives_a_failing_poll(self, tracked, monkeypatch):
        registry, state = tracked
        watcher = ConfigWatcher(registry, state, interval=0.01)
        calls = 0

        def boom():
            nonlocal calls
            calls += 1
            if calls >= 2:
                watcher.stop()
            raise RuntimeError("boom")

        monkeypatch.setattr(watcher, "poll_once", boom)
        watcher.start()
        watcher.join(timeout=3)

        assert calls >= 2
        assert not watcher.is_alive()

    def test_stop_waits_for_the_thread(self, tracked):
        registry, state = tracked
        watcher = ConfigWatcher(registry, state, interval=0.01)
        watcher.start()

        watcher.stop(timeout=2)

        assert not watcher.is_alive()


class TestSourceStatus:
    """An empty name set is disambiguated by the per-source status (#233)."""

    def test_zero_tool_source_is_not_registered_again(self, config_path, monkeypatch):
        from toolregistry import ToolRegistry

        import toolregistry_hub.server.hot_reload as hot_reload

        real = hot_reload.register_python_source
        calls: list[str] = []

        def registers_nothing(reg, source):
            if source.namespace == "calculator":
                calls.append(source.namespace)
                return None
            return real(reg, source)

        monkeypatch.setattr(hot_reload, "register_python_source", registers_nothing)

        config = load_config(str(config_path))
        state = ReloadState(config_path=str(config_path), config=config)
        registry = ToolRegistry(name="status-test")
        reload_registry(registry, state, config)

        calculator = next(k for k in state.source_status if k[1] == "calculator")
        assert state.source_status[calculator] is SourceStatus.APPLIED
        assert state.source_tools[calculator] == frozenset()
        assert calls == ["calculator"]

        # An unrelated edit must not reconnect the applied zero-tool source.
        _write_config(
            config_path,
            '"mode": "denylist", "disabled": [], ' + _sources(CALCULATOR, DATETIME),
        )
        reload_registry(registry, state, load_config(str(config_path)))

        assert calls == ["calculator"]
        assert state.source_status[calculator] is SourceStatus.APPLIED

    def test_excluded_source_becomes_applied_when_in_scope(self, tmp_path):
        path = tmp_path / "tools.jsonc"
        _write_config(
            path,
            '"mode": "allowlist", "enabled": ["calculator"], '
            + _sources(CALCULATOR, DATETIME),
        )
        state = ReloadState()
        registry = build_registry(
            tools_config_path=str(path),
            enable_discovery=False,
            reload_state=state,
        )
        datetime_key = next(k for k in state.source_status if k[1] == "datetime")
        assert state.source_status[datetime_key] is SourceStatus.EXCLUDED
        assert state.source_tools[datetime_key] == frozenset()

        _write_config(path, _sources(CALCULATOR, DATETIME))
        reload_registry(registry, state, load_config(str(path)))

        assert state.source_status[datetime_key] is SourceStatus.APPLIED
        assert "datetime-now" in registry._tools

    def test_failed_source_retries_until_success(
        self, tracked, config_path, monkeypatch
    ):
        import toolregistry_hub.server.hot_reload as hot_reload

        registry, state = tracked
        real = hot_reload.register_python_source
        attempts = 0

        def flaky(reg, source):
            nonlocal attempts
            if source.namespace == "unit_converter":
                attempts += 1
                if attempts < 3:
                    raise RuntimeError("transient failure")
            return real(reg, source)

        monkeypatch.setattr(hot_reload, "register_python_source", flaky)

        _write_config(config_path, _sources(CALCULATOR, DATETIME, UNIT))
        config = load_config(str(config_path))
        reload_registry(registry, state, config)
        key = next(k for k in state.source_status if k[1] == "unit_converter")
        assert state.source_status[key] is SourceStatus.FAILED
        assert key not in state.applied_sources

        reload_registry(registry, state, load_config(str(config_path)))
        assert state.source_status[key] is SourceStatus.FAILED

        reload_registry(registry, state, load_config(str(config_path)))
        assert state.source_status[key] is SourceStatus.APPLIED
        assert "unit_converter-convert" in registry._tools

    def test_failed_reinclusion_retries_on_the_next_reload(self, tmp_path, monkeypatch):
        import toolregistry_hub.server.hot_reload as hot_reload

        path = tmp_path / "tools.jsonc"
        _write_config(
            path,
            '"mode": "allowlist", "enabled": ["calculator"], '
            + _sources(CALCULATOR, DATETIME),
        )
        state = ReloadState()
        registry = build_registry(
            tools_config_path=str(path),
            enable_discovery=False,
            reload_state=state,
        )
        datetime_key = next(k for k in state.source_status if k[1] == "datetime")
        assert state.source_status[datetime_key] is SourceStatus.EXCLUDED

        real = hot_reload.register_python_source
        attempts = 0

        def flaky(reg, source):
            nonlocal attempts
            if source.namespace == "datetime":
                attempts += 1
                if attempts == 1:
                    raise RuntimeError("transient failure")
            return real(reg, source)

        monkeypatch.setattr(hot_reload, "register_python_source", flaky)

        _write_config(path, _sources(CALCULATOR, DATETIME))
        reload_registry(registry, state, load_config(str(path)))
        assert state.source_status[datetime_key] is SourceStatus.FAILED
        assert "datetime-now" not in registry._tools

        reload_registry(registry, state, load_config(str(path)))
        assert state.source_status[datetime_key] is SourceStatus.APPLIED
        assert "datetime-now" in registry._tools
