"""CronTool: scheduled prompt execution with zerodep scheduler.

Provides cron-based task scheduling for agent scenarios. Jobs fire
prompts via a callback injected by the agent runtime. Supports
recurring and one-shot schedules, optional durable persistence,
and automatic 7-day TTL for recurring jobs.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from collections.abc import Callable

from ._scheduler import (
    CronTrigger,
    InvalidCronExpression,
    JobNotFound,
    OnceTrigger,
    Scheduler,
    parse_cron,
)

__all__ = ["CronTool"]

_TTL_DAYS = 7


@dataclass
class _JobRecord:
    """Internal metadata for a scheduled job."""

    job_id: str
    cron_expr: str
    prompt: str
    recurring: bool
    durable: bool
    created_at: str  # ISO 8601


class CronTool:
    """Schedule recurring or one-shot prompts via cron expressions.

    The scheduler runs in a background daemon thread. When a job fires,
    the ``on_trigger`` callback is invoked with the prompt string.
    The agent runtime is responsible for providing this callback.

    Args:
        on_trigger: Callback invoked when a job fires. Receives the
            prompt string. If ``None``, fired prompts are silently
            discarded.
        jobs_file: Path to a JSON file for durable job persistence.
            If ``None``, durable jobs are not supported.
    """

    def __init__(
        self,
        on_trigger: Callable[[str], None] | None = None,
        jobs_file: str | Path | None = None,
    ) -> None:
        self._scheduler = Scheduler(daemon=True)
        self._jobs: dict[str, _JobRecord] = {}
        self._lock = threading.Lock()
        self._on_trigger = on_trigger
        self._jobs_file = Path(jobs_file) if jobs_file else None
        self._scheduler.start()
        self._load_durable()

    def create(
        self,
        cron: str,
        prompt: str,
        recurring: bool = True,
        durable: bool = False,
    ) -> dict:
        """Schedule a prompt to fire on a cron schedule.

        Args:
            cron: Standard 5-field cron expression
                (minute hour day-of-month month day-of-week).
            prompt: The prompt string to deliver when the job fires.
            recurring: If ``True`` (default), fire on every cron match.
                If ``False``, fire once at the next match then auto-delete.
            durable: If ``True``, persist the job to a JSON file so it
                survives process restarts. Requires ``jobs_file`` to be
                set at init time.

        Returns:
            A dict with ``job_id``, ``cron``, ``recurring``, ``durable``,
            and ``next_fire_time``.

        Raises:
            InvalidCronExpression: If *cron* cannot be parsed.
            ValueError: If *durable* is True but no jobs_file was configured.
        """
        if durable and self._jobs_file is None:
            raise ValueError("Cannot create durable job: no jobs_file configured")

        # Validate cron expression (raises InvalidCronExpression on failure)
        spec = parse_cron(cron)

        now = datetime.now()
        job_id = self._generate_id()

        record = _JobRecord(
            job_id=job_id,
            cron_expr=cron,
            prompt=prompt,
            recurring=recurring,
            durable=durable,
            created_at=now.isoformat(),
        )

        if recurring:
            trigger = CronTrigger(cron)
        else:
            # One-shot: compute next fire time from cron, use OnceTrigger
            from ._scheduler import _cron_next_fire_time

            next_time = _cron_next_fire_time(spec, now)
            trigger = OnceTrigger(next_time)

        self._scheduler.add_job(
            self._make_callback(job_id),
            trigger,
            id=job_id,
            name=f"cron-{job_id}",
        )

        with self._lock:
            self._jobs[job_id] = record

        if durable:
            self._save_durable()

        job = self._scheduler.get_job(job_id)
        next_fire = job.next_run_time.isoformat() if job and job.next_run_time else None

        return {
            "job_id": job_id,
            "cron": cron,
            "recurring": recurring,
            "durable": durable,
            "next_fire_time": next_fire,
        }

    def delete(self, job_id: str) -> dict:
        """Cancel a scheduled job.

        Args:
            job_id: The ID returned by ``create()``.

        Returns:
            A dict summarizing the deleted job.

        Raises:
            ValueError: If *job_id* is not found.
        """
        with self._lock:
            record = self._jobs.pop(job_id, None)

        if record is None:
            raise ValueError(f"Job not found: {job_id!r}")

        try:
            self._scheduler.remove_job(job_id)
        except JobNotFound:
            pass  # already removed (e.g. one-shot that already fired)

        if record.durable:
            self._save_durable()

        return {
            "job_id": job_id,
            "cron": record.cron_expr,
            "prompt": record.prompt[:80],
            "deleted": True,
        }

    def list(self) -> str:
        """List all scheduled jobs.

        Returns:
            A text-formatted table of jobs. Returns a message indicating
            no jobs if the list is empty.
        """
        with self._lock:
            records = list(self._jobs.values())

        if not records:
            return "No scheduled jobs."

        lines = [
            f"{'ID':<10} {'Cron':<20} {'Recurring':<10} {'Durable':<8} {'Next Fire':<25} Prompt"
        ]
        lines.append("-" * 100)

        for rec in records:
            job = self._scheduler.get_job(rec.job_id)
            next_fire = (
                job.next_run_time.strftime("%Y-%m-%d %H:%M")
                if job and job.next_run_time
                else "N/A"
            )
            prompt_preview = rec.prompt[:40].replace("\n", " ")
            if len(rec.prompt) > 40:
                prompt_preview += "..."
            lines.append(
                f"{rec.job_id:<10} {rec.cron_expr:<20} {str(rec.recurring):<10} "
                f"{str(rec.durable):<8} {next_fire:<25} {prompt_preview}"
            )

        return "\n".join(lines)

    def shutdown(self) -> None:
        """Stop the scheduler and clean up resources."""
        self._scheduler.shutdown(wait=False)

    # -- Internal helpers --

    def _generate_id(self) -> str:
        """Generate a short unique job ID."""
        import uuid

        return uuid.uuid4().hex[:8]

    def _make_callback(self, job_id: str) -> Callable[[], None]:
        """Create a callback closure for a job.

        The callback checks TTL for recurring jobs and invokes
        ``on_trigger`` with the prompt.
        """

        def _fire() -> None:
            with self._lock:
                record = self._jobs.get(job_id)

            if record is None:
                return

            # TTL check for recurring jobs
            if record.recurring:
                created = datetime.fromisoformat(record.created_at)
                if datetime.now() - created > timedelta(days=_TTL_DAYS):
                    # Expired — remove the job
                    with self._lock:
                        self._jobs.pop(job_id, None)
                    try:
                        self._scheduler.remove_job(job_id)
                    except JobNotFound:
                        pass
                    if record.durable:
                        self._save_durable()
                    return

            # One-shot cleanup: remove from _jobs after firing
            if not record.recurring:
                with self._lock:
                    self._jobs.pop(job_id, None)
                if record.durable:
                    self._save_durable()

            if self._on_trigger is not None:
                self._on_trigger(record.prompt)

        return _fire

    def _save_durable(self) -> None:
        """Persist all durable jobs to the JSON file."""
        if self._jobs_file is None:
            return

        with self._lock:
            durable_records = [
                asdict(rec) for rec in self._jobs.values() if rec.durable
            ]

        self._jobs_file.parent.mkdir(parents=True, exist_ok=True)
        self._jobs_file.write_text(
            json.dumps(durable_records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_durable(self) -> None:
        """Load durable jobs from the JSON file and recreate them."""
        if self._jobs_file is None or not self._jobs_file.exists():
            return

        try:
            data = json.loads(self._jobs_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        for entry in data:
            try:
                record = _JobRecord(**entry)
            except TypeError:
                continue

            # Skip expired jobs
            created = datetime.fromisoformat(record.created_at)
            if record.recurring and datetime.now() - created > timedelta(
                days=_TTL_DAYS
            ):
                continue

            # Recreate the scheduler job
            try:
                spec = parse_cron(record.cron_expr)
            except InvalidCronExpression:
                continue

            now = datetime.now()
            if record.recurring:
                trigger = CronTrigger(record.cron_expr)
            else:
                from ._scheduler import _cron_next_fire_time

                try:
                    next_time = _cron_next_fire_time(spec, now)
                except Exception:
                    continue
                trigger = OnceTrigger(next_time)

            self._scheduler.add_job(
                self._make_callback(record.job_id),
                trigger,
                id=record.job_id,
                name=f"cron-{record.job_id}",
            )

            with self._lock:
                self._jobs[record.job_id] = record

        # Re-save to prune expired entries
        self._save_durable()
