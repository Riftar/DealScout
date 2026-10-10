"""The Dashboard: a small public website where a buyer defines Jobs and reads a Job's
Listing list. It reads only the Job store, so Snapshots are never within its reach."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pydantic import ValidationError

from dealscout.dashboard import pages
from dealscout.dashboard.schedule import JAKARTA
from dealscout.dashboard.store import JobStore
from dealscout.domain import JOB_PORTALS, Brief, Job, RunTrigger, normalize_area

MAX_BODY_BYTES = 16_384
# The site is public and every Run spends model money and Portal requests.
MAX_ACTIVE_JOBS = int(os.environ.get("DASHBOARD_MAX_ACTIVE_JOBS", "20"))
MAX_RUN_NOW_PER_DAY = int(os.environ.get("DASHBOARD_MAX_RUN_NOW_PER_DAY", "3"))

_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; form-action 'self'; base-uri 'none'; "
        "frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

_BUDGET = re.compile(r"^(?:rp\.?)?\s*([\d.,]+)\s*(juta|jt|miliar|milyar|m)?$", re.I)


@dataclass
class Response:
    status: int
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def redirect(cls, location: str) -> Response:
        return cls(303, "", {"Location": location})


def parse_budget(text: str) -> int | None:
    """Whole Rupiah from '1500000000', '1.500.000.000', '850 juta' or '1,5 miliar'."""
    match = _BUDGET.match(text.strip())
    if not match:
        return None
    number, unit = match.group(1), (match.group(2) or "").lower()
    if not unit:
        digits = re.sub(r"\D", "", number)
        return int(digits) if digits else None
    try:
        amount = float(number.replace(",", "."))
    except ValueError:
        return None
    return round(amount * (1_000_000 if unit in ("juta", "jt") else 1_000_000_000))


def _number(form: dict, name: str, errors: dict, *, whole: bool = False) -> float | int | None:
    raw = _first(form, name).replace(",", ".")
    if not raw:
        return None
    try:
        value = int(raw) if whole else float(raw)
    except ValueError:
        errors[name] = "Type a number, or leave it empty."
        return None
    if value < 0 or (value == 0 and not whole):
        errors[name] = "Type a number above zero, or leave it empty."
        return None
    return value


def _first(form: dict[str, list[str]], name: str) -> str:
    return (form.get(name) or [""])[0].strip()


def parse_job_form(form: dict[str, list[str]]) -> tuple[dict, dict[str, str], dict | None]:
    """Returns the values to show again, the errors, and the parsed Job parts when valid."""
    errors: dict[str, str] = {}
    values: dict[str, object] = {
        name: _first(form, name)
        for name in ("area", "budget", "headroom", "land_m2", "building_m2", "bedrooms", "daily_time")
    }
    portals = [name for name in form.get("portals", []) if name in JOB_PORTALS]
    values["portals"] = portals

    area_text = str(values["area"])[:60]
    if not area_text:
        errors["area"] = "Name the Area the house should be in."
    budget = parse_budget(str(values["budget"]))
    if not budget:
        errors["budget"] = "Type the budget in Rupiah, for example 850 juta."
    try:
        headroom = int(str(values["headroom"]) or "5") / 100
    except ValueError:
        headroom = 0.05
    land = _number(form, "land_m2", errors)
    building = _number(form, "building_m2", errors)
    bedrooms = _number(form, "bedrooms", errors, whole=True)
    if not portals:
        errors["portals"] = "Pick at least one Portal."
    daily_time = str(values["daily_time"])[:5]
    if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", daily_time):
        errors["daily_time"] = "Pick the time of the daily Run."
    if errors:
        return values, errors, None
    try:
        brief = Brief(
            area=normalize_area(area_text) or area_text,
            budget_rp=budget,
            headroom=headroom,
            land_m2=land,
            building_m2=building,
            bedrooms=bedrooms,
        )
    except ValidationError as error:
        for issue in error.errors():
            name = {"budget_rp": "budget"}.get(str(issue["loc"][0]), str(issue["loc"][0]))
            errors[name] = "That value is out of range."
        return values, errors, None
    return values, errors, {
        "brief": brief,
        "area_text": area_text,
        "portals": portals,
        "daily_time": daily_time,
    }


def form_values(job: Job) -> dict[str, object]:
    brief = job.brief
    return {
        "area": job.area_text,
        "budget": str(brief.budget_rp),
        "headroom": str(round(brief.headroom * 100)),
        "land_m2": f"{brief.land_m2:g}" if brief.land_m2 else "",
        "building_m2": f"{brief.building_m2:g}" if brief.building_m2 else "",
        "bedrooms": "" if brief.bedrooms is None else str(brief.bedrooms),
        "portals": job.portals,
        "daily_time": job.daily_time,
    }


class Dashboard:
    def __init__(
        self,
        store: JobStore,
        *,
        kick: Callable[[], None] = lambda: None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self.store = store
        self.kick = kick  # start a tick, so Run now does not wait for cron
        self.now = now

    def handle(self, method: str, target: str, form: dict[str, list[str]] | None = None) -> Response:
        form = form or {}
        parts = urlsplit(target)
        path = parts.path.rstrip("/") or "/"
        query = parse_qs(parts.query)
        if method in ("GET", "HEAD"):
            if path == "/":
                return self._home()
            if path == "/healthz":
                return Response(200, "ok")
            if path == "/jobs/new":
                blank = {"headroom": "5", "daily_time": "06:00", "portals": ["rumah123", "99co"]}
                return self._html(pages.job_form(blank, {}, action="/jobs"))
            if match := re.fullmatch(r"/jobs/(\d{1,9})", path):
                return self._job(int(match[1]), _first(query, "run"), _first(query, "notice"))
            if match := re.fullmatch(r"/jobs/(\d{1,9})/edit", path):
                job = self.store.get_job(int(match[1]))
                if job is None:
                    return self._missing()
                return self._html(pages.job_form(form_values(job), {}, action=f"/jobs/{job.id}", editing=job))
        elif method == "POST":
            if path == "/jobs":
                return self._create(form)
            if match := re.fullmatch(r"/jobs/(\d{1,9})(/run|/active)?", path):
                job = self.store.get_job(int(match[1]))
                if job is None:
                    return self._missing()
                if match[2] == "/run":
                    return self._run_now(job)
                if match[2] == "/active":
                    return self._set_active(job, _first(form, "active") == "1")
                return self._change(job, form)
        else:
            return Response(405, "method not allowed", {"Allow": "GET, HEAD, POST"})
        return self._missing()

    def _html(self, body: str, status: int = 200) -> Response:
        return Response(status, body, {"Content-Type": "text/html; charset=utf-8"})

    def _missing(self) -> Response:
        return self._html(pages.message("Not found", "There is nothing at this address."), 404)

    def _home(self) -> Response:
        jobs = self.store.list_jobs()
        last = {job.id: next(iter(self.store.runs_for(job.id, limit=1)), None) for job in jobs}
        return self._html(pages.home(jobs, last))

    _NOTICES = {
        "busy": "This Job already has a Run waiting or going.",
        "limit": "This Job has used its Run now turns for today. The daily Run still happens.",
        "full": "The Dashboard has as many running Jobs as it can hold. Stop one to resume this one.",
    }

    def _job(self, job_id: int, run_param: str, notice: str) -> Response:
        job = self.store.get_job(job_id)
        if job is None:
            return self._missing()
        runs = self.store.runs_for(job.id)
        shown = None
        if run_param.isdigit():
            shown = self.store.get_run(int(run_param))
            if shown is not None and shown.job_id != job.id:
                shown = None
        shown = shown or self.store.latest_done(job.id)
        replaced_by = next((j.id for j in self.store.list_jobs() if j.replaces == job.id), None)
        return self._html(
            pages.job_page(job, runs, shown, replaced_by=replaced_by, notice=self._NOTICES.get(notice))
        )

    def _create(self, form: dict[str, list[str]]) -> Response:
        values, errors, parsed = parse_job_form(form)
        if parsed is not None and self.store.count_active() >= MAX_ACTIVE_JOBS:
            errors["daily_time"] = self._NOTICES["full"]
        if errors or parsed is None:
            return self._html(pages.job_form(values, errors, action="/jobs"), 422)
        job = self.store.add_job(Job(**parsed, created_at=self.now()))
        return Response.redirect(f"/jobs/{job.id}")

    def _change(self, job: Job, form: dict[str, list[str]]) -> Response:
        values, errors, parsed = parse_job_form(form)
        if errors or parsed is None:
            return self._html(
                pages.job_form(values, errors, action=f"/jobs/{job.id}", editing=job), 422
            )
        if parsed["brief"] == job.brief:
            self.store.update_schedule(job.id, parsed["portals"], parsed["daily_time"])
            return Response.redirect(f"/jobs/{job.id}")
        if _first(form, "confirm") != "1":
            hidden = {name: items for name, items in form.items() if name != "confirm"}
            return self._html(pages.confirm_new_job(job, parsed["brief"], hidden))
        # Any Brief change is a new Job. The old one keeps its Listing list and stops firing.
        self.store.set_active(job.id, False)
        new_job = self.store.add_job(Job(**parsed, created_at=self.now(), replaces=job.id))
        return Response.redirect(f"/jobs/{new_job.id}")

    def _run_now(self, job: Job) -> Response:
        if self.store.has_open_run(job.id):
            return Response.redirect(f"/jobs/{job.id}?notice=busy")
        midnight = self.now().astimezone(JAKARTA).replace(hour=0, minute=0, second=0, microsecond=0)
        if self.store.count_runs_since(job.id, RunTrigger.NOW, midnight.astimezone(UTC)) >= MAX_RUN_NOW_PER_DAY:
            return Response.redirect(f"/jobs/{job.id}?notice=limit")
        self.store.enqueue(job.id, RunTrigger.NOW, self.now())
        self.kick()
        return Response.redirect(f"/jobs/{job.id}")

    def _set_active(self, job: Job, active: bool) -> Response:
        if active and not job.active and self.store.count_active() >= MAX_ACTIVE_JOBS:
            return Response.redirect(f"/jobs/{job.id}?notice=full")
        self.store.set_active(job.id, active)
        return Response.redirect(f"/jobs/{job.id}")


def spawn_tick(state_dir: Path) -> Callable[[], None]:
    """A kick that starts `dealscout tick` as its own process, logging beside the Job store."""

    def kick() -> None:
        with (state_dir / "tick.log").open("ab") as log:
            subprocess.Popen(
                [sys.executable, "-m", "dealscout.run.cli", "tick", "--state-dir", str(state_dir)],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
            )

    return kick


def serve(dashboard: Dashboard, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        server_version = "DealScout"
        sys_version = ""

        def _reply(self, response: Response) -> None:
            body = response.body.encode("utf-8")
            self.send_response(response.status)
            for name, value in {"Content-Type": "text/plain; charset=utf-8", **_HEADERS, **response.headers}.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_GET(self) -> None:
            self._reply(dashboard.handle(self.command, self.path))

        do_HEAD = do_GET

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY_BYTES:
                self.close_connection = True
                self._reply(Response(413, "request too large"))
                return
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            self._reply(dashboard.handle("POST", self.path, parse_qs(body, keep_blank_values=True)))

    ThreadingHTTPServer((host, port), Handler).serve_forever()

