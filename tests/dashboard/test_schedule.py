from datetime import UTC, datetime, timedelta

import pytest

from dealscout.dashboard.schedule import due_date, enqueue_due, job_urls, tick
from dealscout.dashboard.store import JobStore
from dealscout.domain import JobRunState, RunTrigger
from dealscout.value.market import market_price
from dealscout.value.valuation import value
from tests.dashboard.helpers import T0, a_job, a_record, final_state


def _wib(hour: int, minute: int = 0, day: int = 11) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=UTC) - timedelta(hours=7)


def test_job_is_due_once_its_jakarta_time_has_come():
    job = a_job(daily_time="06:00", created_at=_wib(20, day=10))
    assert due_date(job, _wib(5, 59)) is None
    assert due_date(job, _wib(6, 0)).isoformat() == "2026-10-11"
    assert due_date(job, _wib(23, 30)).isoformat() == "2026-10-11"


def test_job_made_after_the_daily_time_first_fires_tomorrow():
    job = a_job(daily_time="06:00", created_at=_wib(8))
    assert due_date(job, _wib(9)) is None
    assert due_date(job, _wib(6, 1, day=12)).isoformat() == "2026-10-12"


def test_stopped_job_is_never_due():
    assert due_date(a_job(active=False, created_at=_wib(20, day=10)), _wib(7)) is None


def test_due_jobs_are_queued_once_a_day(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    store.add_job(a_job(created_at=_wib(20, day=10)))
    assert enqueue_due(store, _wib(6, 1)) == 1
    assert enqueue_due(store, _wib(6, 2)) == 0
    assert enqueue_due(store, _wib(6, 1, day=12)) == 1


def test_job_urls_keep_only_the_chosen_portals(tmp_path):
    (tmp_path / "a.txt").write_text(
        "# note\nhttps://www.rumah123.com/a\nhttps://www.99.co/b\nhttps://www.olx.co.id/c\n"
        "https://www.rumah123.com/a\n",
        encoding="utf-8",
    )
    assert job_urls(a_job(portals=["rumah123"]), tmp_path) == ["https://www.rumah123.com/a"]


def _never(*_):
    pytest.fail("no Run should be carried out")


def _tick(store, tmp_path, execute, kicks=None):
    return tick(
        store,
        execute=execute,
        market_price=market_price,
        value=value,
        urls_dir=tmp_path,
        runs_dir=tmp_path / "runs",
        now=lambda: T0,
        kick=lambda: kicks.append(1) if kicks is not None else None,
    )


def test_tick_carries_out_one_run_and_saves_the_listing_list(tmp_path):
    (tmp_path / "urls.txt").write_text(
        "https://www.rumah123.com/a\nhttps://www.pinhome.id/x\n", encoding="utf-8"
    )
    store = JobStore(tmp_path / "jobs.sqlite")
    job = store.add_job(a_job())
    store.enqueue(job.id, RunTrigger.NOW, T0)
    store.enqueue(job.id, RunTrigger.NOW, T0)
    calls, kicks = [], []

    def execute(brief, urls, out_dir, thread_id):
        calls.append((brief.area, urls, thread_id))
        return final_state([a_record(n, 900_000_000 + n * 50_000_000) for n in range(4)]), "trace-1"

    run = _tick(store, tmp_path, execute, kicks)

    assert calls == [("Bintaro", ["https://www.rumah123.com/a"], "job-1-run-1")]
    assert run.state is JobRunState.DONE and run.trace_id == "trace-1"
    assert len(run.listing_list.rows) == 4
    assert kicks == [1]  # a second Run is still queued


def test_tick_marks_a_failed_run_without_leaking_the_error(tmp_path):
    (tmp_path / "urls.txt").write_text("https://www.rumah123.com/a\n", encoding="utf-8")
    store = JobStore(tmp_path / "jobs.sqlite")
    job = store.add_job(a_job())
    store.enqueue(job.id, RunTrigger.NOW, T0)

    def execute(*_):
        raise RuntimeError("LLM_API_KEY=sk-secret rejected")

    run = _tick(store, tmp_path, execute)
    assert run.state is JobRunState.FAILED
    assert "secret" not in run.error and "RuntimeError" in run.error


def test_tick_with_no_urls_for_the_portals_fails_the_run(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    job = store.add_job(a_job())
    store.enqueue(job.id, RunTrigger.NOW, T0)
    run = _tick(store, tmp_path, _never)
    assert run.state is JobRunState.FAILED and "no Listing URLs" in run.error


def test_tick_does_nothing_when_nothing_is_due(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    store.add_job(a_job())  # made at 08:00 WIB, daily time 06:00
    assert _tick(store, tmp_path, _never) is None
