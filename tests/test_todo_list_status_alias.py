"""Tests for status aliasing in ``TodoList`` (issue #116)."""

from __future__ import annotations

import pytest

from toolregistry_hub.todo_list import TodoList


class TestInProgressAlias:
    def test_in_progress_accepted_as_pending(self):
        # The user-facing string format passes through unchanged on simple
        # output, but the parsed row should report the canonical status.
        result = TodoList.update(["[task1] do thing (in_progress)"], format="markdown")
        assert "pending" in (result or "")
        assert "in_progress" not in (result or "")

    @pytest.mark.parametrize("alias", ["in_progress", "in-progress", "inprogress"])
    def test_aliases_normalize_to_pending(self, alias):
        parsed = TodoList._parse_simple_format(f"[t] task ({alias})")
        assert parsed["status"] == "pending"

    def test_unknown_status_still_rejected(self):
        with pytest.raises(ValueError, match="Invalid status"):
            TodoList.update(["[t] thing (working)"], format="simple")

    def test_existing_canonical_statuses_unchanged(self):
        # Regression guard: the four canonical names must keep working.
        for status in ("planned", "pending", "done", "cancelled"):
            parsed = TodoList._parse_simple_format(f"[t] task ({status})")
            assert parsed["status"] == status
