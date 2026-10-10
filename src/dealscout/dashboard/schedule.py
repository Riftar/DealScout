"""Fire Jobs: queue the ones due today, then carry out one queued Run.

`dealscout tick` calls this every minute from cron. Each Job fires once a day at its own
time in Asia/Jakarta, and "Run now" on the Dashboard queues one more.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

from dealscout.collect.fetcher import portal_of
from dealscout.dashboard.listing_list import build_listing_list
from dealscout.dashboard.store import JobStore
from dealscout.domain import Brief, Job, JobRun, RunTrigger

# Asia/Jakarta has no daylight saving, so a fixed offset needs no tz database.
JAKARTA = timezone(timedelta(hours=7), "WIB")

# (brief, urls, out_dir, thread_id) -> (final Run state, neatlogs trace id)
Execute = Callable[[Brief, list[str], Path, str], tuple[dict, str | None]]


def due_date(job: Job, now: datetime) -> date | None:
    """The Jakarta date whose daily firing has come, or None. A Job made after today's time
    first fires tomorrow; the buyer has Run now for a first list."""
    local = now.astimezone(JAKARTA)
    hour, minute = (int(part) for part in job.daily_time.split(":"))
    firing = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if not job.active or firing > local or firing < job.created_at:
        return None
    return local.date()


def enqueue_due(store: JobStore, now: datetime) -> int:
    queued = 0
    for job in store.list_jobs():
        day = due_date(job, now)
        if day is not None and store.enqueue(job.id, RunTrigger.DAILY, now, scheduled_for=day):
            queued += 1
    return queued


def read_urls(path: Path) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def job_urls(job: Job, urls_dir: Path) -> list[str]:
    """The corpus Listing URLs on the Job's Portals. Portal search pages are not crawled."""
    urls: dict[str, None] = {}
    for path in sorted(Path(urls_dir).glob("*.txt")):
        for url in read_urls(path):
            if portal_of(url) in job.portals:
                urls.setdefault(url)
    return list(urls)


def tick(
    store: JobStore,
    *,
    execute: Execute,
    market_price: Callable,
    value: Callable,
    urls_dir: Path = Path("data/urls"),
    runs_dir: Path = Path("data/runs"),
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    kick: Callable[[], None] = lambda: None,
) -> JobRun | None:
    """Queue due Jobs and carry out at most one Run. Returns the Run it carried out."""
    enqueue_due(store, now())
    run = store.claim_next(now())
    if run is None:
        return None
    job = store.get_job(run.job_id)
    try:
        urls = job_urls(job, urls_dir)
        if not urls:
            raise NoListings("no Listing URLs are on file for this Job's Portals")
        out_dir = Path(runs_dir) / f"job-{job.id}" / f"run-{run.id}"
        final, trace_id = execute(job.brief, urls, out_dir, f"job-{job.id}-run-{run.id}")
        listing_list = build_listing_list(job, final, market_price=market_price, value=value)
        store.finish(run.id, now(), listing_list=listing_list, trace_id=trace_id)
    except NoListings as error:
        store.finish(run.id, now(), error=str(error))
    except Exception as error:
        # The Dashboard is public: show the kind of failure, keep the detail in the tick log.
        print(f"run {run.id} of job {job.id} failed: {error!r}", flush=True)
        store.finish(run.id, now(), error=f"the Run failed ({type(error).__name__})")
    if store.queued_count():
        kick()
    return store.get_run(run.id)


class NoListings(Exception):
    pass
