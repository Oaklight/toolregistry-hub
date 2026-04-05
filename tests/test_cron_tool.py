"""Tests for CronTool scheduled prompt execution."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from toolregistry_hub.cron_tool import CronTool, _TTL_DAYS


@pytest.fixture
def cron_tool():
    """Create a CronTool instance with a mock callback."""
    callback = MagicMock()
    tool = CronTool(on_trigger=callback)
    yield tool, callback
    tool.shutdown()


@pytest.fixture
def cron_tool_durable(tmp_path):
    """Create a CronTool instance with durable persistence."""
    jobs_file = tmp_path / "scheduled_tasks.json"
    callback = MagicMock()
    tool = CronTool(on_trigger=callback, jobs_file=jobs_file)
    yield tool, callback, jobs_file
    tool.shutdown()


class TestCreate:
    def test_create_recurring_job(self, cron_tool):
        tool, _ = cron_tool
        result = tool.create("*/5 * * * *", "check build status")

        assert "job_id" in result
        assert result["cron"] == "*/5 * * * *"
        assert result["recurring"] is True
        assert result["durable"] is False
        assert result["next_fire_time"] is not None

    def test_create_one_shot_job(self, cron_tool):
        tool, _ = cron_tool
        result = tool.create("0 9 * * *", "morning reminder", recurring=False)

        assert result["recurring"] is False
        assert result["next_fire_time"] is not None

    def test_create_durable_job(self, cron_tool_durable):
        tool, _, jobs_file = cron_tool_durable
        result = tool.create("0 9 * * 1-5", "weekday check", durable=True)

        assert result["durable"] is True
        assert jobs_file.exists()
        data = json.loads(jobs_file.read_text())
        assert len(data) == 1
        assert data[0]["job_id"] == result["job_id"]

    def test_create_durable_without_jobs_file(self, cron_tool):
        tool, _ = cron_tool
        with pytest.raises(ValueError, match="no jobs_file configured"):
            tool.create("0 9 * * *", "test", durable=True)

    def test_create_invalid_cron(self, cron_tool):
        tool, _ = cron_tool
        with pytest.raises(Exception):
            tool.create("invalid cron", "test")

    def test_create_invalid_cron_wrong_fields(self, cron_tool):
        tool, _ = cron_tool
        with pytest.raises(Exception):
            tool.create("* * *", "test")  # only 3 fields


class TestDelete:
    def test_delete_existing_job(self, cron_tool):
        tool, _ = cron_tool
        result = tool.create("*/10 * * * *", "periodic task")
        job_id = result["job_id"]

        deleted = tool.delete(job_id)
        assert deleted["job_id"] == job_id
        assert deleted["deleted"] is True

    def test_delete_nonexistent_job(self, cron_tool):
        tool, _ = cron_tool
        with pytest.raises(ValueError, match="Job not found"):
            tool.delete("nonexistent")

    def test_delete_durable_job_updates_file(self, cron_tool_durable):
        tool, _, jobs_file = cron_tool_durable
        result = tool.create("0 9 * * *", "to delete", durable=True)

        tool.delete(result["job_id"])

        data = json.loads(jobs_file.read_text())
        assert len(data) == 0


class TestList:
    def test_list_empty(self, cron_tool):
        tool, _ = cron_tool
        output = tool.list()
        assert "No scheduled jobs" in output

    def test_list_with_jobs(self, cron_tool):
        tool, _ = cron_tool
        tool.create("*/5 * * * *", "job one")
        tool.create("0 9 * * *", "job two")

        output = tool.list()
        assert "job one" in output
        assert "job two" in output
        assert "*/5 * * * *" in output
        assert "0 9 * * *" in output

    def test_list_after_delete(self, cron_tool):
        tool, _ = cron_tool
        tool.create("*/5 * * * *", "keep this")
        r2 = tool.create("0 9 * * *", "delete this")

        tool.delete(r2["job_id"])
        output = tool.list()

        assert "keep this" in output
        assert "delete this" not in output


class TestCallback:
    def test_callback_invoked_on_fire(self):
        """Verify on_trigger is called when a job fires."""
        callback = MagicMock()
        tool = CronTool(on_trigger=callback)

        try:
            # Use a very short interval via cron that matches every minute
            # To avoid waiting, manually invoke the callback mechanism
            result = tool.create("* * * * *", "fire now")
            job_id = result["job_id"]

            # Directly invoke the scheduler job to simulate firing
            tool._scheduler.run_job(job_id)

            callback.assert_called_once_with("fire now")
        finally:
            tool.shutdown()

    def test_no_callback_when_none(self):
        """Verify no error when on_trigger is None."""
        tool = CronTool(on_trigger=None)
        try:
            result = tool.create("* * * * *", "no callback")
            tool._scheduler.run_job(result["job_id"])
            # Should not raise
        finally:
            tool.shutdown()


class TestTTL:
    def test_recurring_job_expires_after_ttl(self):
        """Verify recurring jobs are removed after 7 days."""
        callback = MagicMock()
        tool = CronTool(on_trigger=callback)

        try:
            result = tool.create("* * * * *", "will expire")
            job_id = result["job_id"]

            # Patch the created_at to 8 days ago
            with tool._lock:
                record = tool._jobs[job_id]
                record.created_at = (
                    datetime.now() - timedelta(days=_TTL_DAYS + 1)
                ).isoformat()

            # Fire the job — TTL check should remove it
            tool._scheduler.run_job(job_id)

            callback.assert_not_called()
            assert job_id not in tool._jobs
        finally:
            tool.shutdown()

    def test_recurring_job_within_ttl_fires(self):
        """Verify recurring jobs within TTL still fire."""
        callback = MagicMock()
        tool = CronTool(on_trigger=callback)

        try:
            result = tool.create("* * * * *", "still valid")
            job_id = result["job_id"]

            tool._scheduler.run_job(job_id)

            callback.assert_called_once_with("still valid")
            assert job_id in tool._jobs
        finally:
            tool.shutdown()


class TestOneShot:
    def test_one_shot_removed_after_fire(self):
        """Verify one-shot jobs are removed from _jobs after firing."""
        callback = MagicMock()
        tool = CronTool(on_trigger=callback)

        try:
            result = tool.create("* * * * *", "once only", recurring=False)
            job_id = result["job_id"]

            tool._scheduler.run_job(job_id)

            callback.assert_called_once_with("once only")
            assert job_id not in tool._jobs
        finally:
            tool.shutdown()


class TestDurablePersistence:
    def test_load_durable_on_init(self, tmp_path):
        """Verify durable jobs are restored on init."""
        jobs_file = tmp_path / "tasks.json"
        callback = MagicMock()

        # Create a tool and add a durable job
        tool1 = CronTool(on_trigger=callback, jobs_file=jobs_file)
        result = tool1.create("0 9 * * *", "persistent job", durable=True)
        job_id = result["job_id"]
        tool1.shutdown()

        # Create a new tool instance — should reload the job
        tool2 = CronTool(on_trigger=callback, jobs_file=jobs_file)
        try:
            assert job_id in tool2._jobs
            output = tool2.list()
            assert "persistent job" in output
        finally:
            tool2.shutdown()

    def test_expired_durable_jobs_pruned_on_load(self, tmp_path):
        """Verify expired durable jobs are not loaded."""
        jobs_file = tmp_path / "tasks.json"

        expired_record = {
            "job_id": "expired1",
            "cron_expr": "0 9 * * *",
            "prompt": "old job",
            "recurring": True,
            "durable": True,
            "created_at": (datetime.now() - timedelta(days=_TTL_DAYS + 1)).isoformat(),
        }
        jobs_file.write_text(json.dumps([expired_record]))

        tool = CronTool(jobs_file=jobs_file)
        try:
            assert "expired1" not in tool._jobs
        finally:
            tool.shutdown()

    def test_non_durable_jobs_not_persisted(self, cron_tool_durable):
        tool, _, jobs_file = cron_tool_durable
        tool.create("0 9 * * *", "durable one", durable=True)
        tool.create("0 10 * * *", "ephemeral one", durable=False)

        data = json.loads(jobs_file.read_text())
        assert len(data) == 1
        assert data[0]["prompt"] == "durable one"
