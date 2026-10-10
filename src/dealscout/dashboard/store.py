"""Jobs and their Runs in one SQLite file on the instance disk."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

from dealscout.domain import Brief, Job, JobRun, JobRunState, ListingList, RunTrigger

# A Run still marked running after this long belongs to a process that died.
STALE_AFTER = timedelta(hours=2)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief TEXT NOT NULL,
    area_text TEXT NOT NULL,
    portals TEXT NOT NULL,
    daily_time TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    replaces INTEGER
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    trigger TEXT NOT NULL,
    scheduled_for TEXT,
    state TEXT NOT NULL,
    queued_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    trace_id TEXT,
    error TEXT,
    listing_list TEXT,
    UNIQUE (job_id, scheduled_for)
);
"""

_RUN_COLUMNS = "id, job_id, trigger, state, queued_at, started_at, finished_at, trace_id, error"


def _job(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        brief=Brief.model_validate_json(row["brief"]),
        area_text=row["area_text"],
        portals=json.loads(row["portals"]),
        daily_time=row["daily_time"],
        active=bool(row["active"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        replaces=row["replaces"],
    )


def _run(row: sqlite3.Row) -> JobRun:
    body = dict(row)
    listing_list = body.pop("listing_list", None)
    return JobRun(
        **body,
        listing_list=ListingList.model_validate_json(listing_list) if listing_list else None,
    )


class JobStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(_SCHEMA)

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    # Jobs

    def add_job(self, job: Job) -> Job:
        with self._db() as db:
            cursor = db.execute(
                "INSERT INTO jobs (brief, area_text, portals, daily_time, active, created_at, replaces)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    job.brief.model_dump_json(),
                    job.area_text,
                    json.dumps(job.portals),
                    job.daily_time,
                    int(job.active),
                    job.created_at.isoformat(),
                    job.replaces,
                ),
            )
        return job.model_copy(update={"id": cursor.lastrowid})

    def get_job(self, job_id: int) -> Job | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _job(row) if row else None

    def list_jobs(self) -> list[Job]:
        with self._db() as db:
            rows = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        return [_job(row) for row in rows]

    def count_active(self) -> int:
        with self._db() as db:
            return db.execute("SELECT COUNT(*) FROM jobs WHERE active = 1").fetchone()[0]

    def update_schedule(self, job_id: int, portals: list[str], daily_time: str) -> None:
        with self._db() as db:
            db.execute(
                "UPDATE jobs SET portals = ?, daily_time = ? WHERE id = ?",
                (json.dumps(portals), daily_time, job_id),
            )

    def set_active(self, job_id: int, active: bool) -> None:
        with self._db() as db:
            db.execute("UPDATE jobs SET active = ? WHERE id = ?", (int(active), job_id))

    # Runs

    def enqueue(
        self, job_id: int, trigger: RunTrigger, now: datetime, scheduled_for: date | None = None
    ) -> int | None:
        """Queue a Run. A daily Run already queued for that date is not queued twice."""
        with self._db() as db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO runs (job_id, trigger, scheduled_for, state, queued_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    job_id,
                    trigger.value,
                    scheduled_for.isoformat() if scheduled_for else None,
                    JobRunState.QUEUED.value,
                    now.isoformat(),
                ),
            )
            return cursor.lastrowid if cursor.rowcount else None

    def has_open_run(self, job_id: int) -> bool:
        with self._db() as db:
            row = db.execute(
                "SELECT 1 FROM runs WHERE job_id = ? AND state IN ('queued', 'running') LIMIT 1",
                (job_id,),
            ).fetchone()
        return row is not None

    def count_runs_since(self, job_id: int, trigger: RunTrigger, since: datetime) -> int:
        with self._db() as db:
            return db.execute(
                "SELECT COUNT(*) FROM runs WHERE job_id = ? AND trigger = ? AND queued_at >= ?",
                (job_id, trigger.value, since.isoformat()),
            ).fetchone()[0]

    def queued_count(self) -> int:
        with self._db() as db:
            return db.execute("SELECT COUNT(*) FROM runs WHERE state = 'queued'").fetchone()[0]

    def claim_next(self, now: datetime) -> JobRun | None:
        """Take the oldest queued Run, unless another Run is still going. One Run at a time
        keeps a single Fetcher, and so one crawl delay, per Portal."""
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE runs SET state = 'failed', finished_at = ?, error = ?"
                " WHERE state = 'running' AND started_at < ?",
                (now.isoformat(), "the Run stopped before it finished", (now - STALE_AFTER).isoformat()),
            )
            busy = db.execute("SELECT 1 FROM runs WHERE state = 'running' LIMIT 1").fetchone()
            row = None
            if not busy:
                row = db.execute(
                    f"SELECT {_RUN_COLUMNS} FROM runs WHERE state = 'queued' ORDER BY id LIMIT 1"
                ).fetchone()
            if row is not None:
                db.execute(
                    "UPDATE runs SET state = 'running', started_at = ? WHERE id = ?",
                    (now.isoformat(), row["id"]),
                )
            db.execute("COMMIT")
        if row is None:
            return None
        return _run(row).model_copy(update={"state": JobRunState.RUNNING, "started_at": now})

    def finish(
        self,
        run_id: int,
        now: datetime,
        *,
        listing_list: ListingList | None = None,
        trace_id: str | None = None,
        error: str | None = None,
    ) -> None:
        state = JobRunState.FAILED if error else JobRunState.DONE
        with self._db() as db:
            db.execute(
                "UPDATE runs SET state = ?, finished_at = ?, trace_id = ?, error = ?, listing_list = ?"
                " WHERE id = ?",
                (
                    state.value,
                    now.isoformat(),
                    trace_id,
                    error,
                    listing_list.model_dump_json() if listing_list else None,
                    run_id,
                ),
            )

    def runs_for(self, job_id: int, limit: int = 10) -> list[JobRun]:
        """A Job's latest Runs, newest first, without their Listing lists."""
        with self._db() as db:
            rows = db.execute(
                f"SELECT {_RUN_COLUMNS} FROM runs WHERE job_id = ? ORDER BY id DESC LIMIT ?",
                (job_id, limit),
            ).fetchall()
        return [_run(row) for row in rows]

    def get_run(self, run_id: int) -> JobRun | None:
        with self._db() as db:
            row = db.execute(
                f"SELECT {_RUN_COLUMNS}, listing_list FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
        return _run(row) if row else None

    def latest_done(self, job_id: int) -> JobRun | None:
        with self._db() as db:
            row = db.execute(
                f"SELECT {_RUN_COLUMNS}, listing_list FROM runs"
                " WHERE job_id = ? AND state = 'done' ORDER BY id DESC LIMIT 1",
                (job_id,),
            ).fetchone()
        return _run(row) if row else None
