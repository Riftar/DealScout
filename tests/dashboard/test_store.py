from datetime import date, timedelta

from dealscout.dashboard.store import STALE_AFTER, JobStore
from dealscout.domain import JobRunState, ListingList, RunTrigger
from tests.dashboard.helpers import T0, a_job


def test_job_round_trips(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    saved = store.add_job(a_job())
    assert saved.id == 1
    assert store.get_job(1) == saved
    assert store.list_jobs() == [saved]
    assert store.get_job(99) is None


def test_daily_run_is_queued_once_per_date(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    job = store.add_job(a_job())
    day = date(2026, 10, 11)
    assert store.enqueue(job.id, RunTrigger.DAILY, T0, scheduled_for=day) is not None
    assert store.enqueue(job.id, RunTrigger.DAILY, T0, scheduled_for=day) is None
    assert store.enqueue(job.id, RunTrigger.NOW, T0) is not None
    assert store.enqueue(job.id, RunTrigger.NOW, T0) is not None
    assert store.queued_count() == 3


def test_one_run_at_a_time_and_stale_runs_fail(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    job = store.add_job(a_job())
    first = store.enqueue(job.id, RunTrigger.NOW, T0)
    second = store.enqueue(job.id, RunTrigger.NOW, T0)

    assert store.claim_next(T0).id == first
    assert store.claim_next(T0 + timedelta(minutes=5)) is None  # the first is still going

    later = T0 + STALE_AFTER + timedelta(minutes=1)
    assert store.claim_next(later).id == second
    assert store.get_run(first).state is JobRunState.FAILED


def test_finished_run_keeps_its_listing_list(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite")
    job = store.add_job(a_job())
    run_id = store.enqueue(job.id, RunTrigger.NOW, T0)
    store.claim_next(T0)
    store.finish(run_id, T0, listing_list=ListingList(confirmed=4), trace_id="abc")

    done = store.latest_done(job.id)
    assert done.state is JobRunState.DONE and done.trace_id == "abc"
    assert done.listing_list.confirmed == 4
    assert store.runs_for(job.id)[0].listing_list is None
    assert not store.has_open_run(job.id)
