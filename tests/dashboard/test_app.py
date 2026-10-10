from urllib.parse import parse_qs, urlencode

import pytest

from dealscout.dashboard import app as app_module
from dealscout.dashboard.app import Dashboard, parse_budget
from dealscout.dashboard.listing_list import build_listing_list
from dealscout.dashboard.store import JobStore
from dealscout.domain import RunTrigger, Status
from dealscout.value.market import market_price
from dealscout.value.valuation import value
from tests.dashboard.helpers import T0, a_job, a_record, final_state

FORM = {
    "area": "bintaro jaya",
    "budget": "1,5 miliar",
    "headroom": "5",
    "land_m2": "",
    "building_m2": "",
    "bedrooms": "3",
    "portals": ["rumah123", "99co"],
    "daily_time": "06:30",
}


def _form(**changes) -> dict[str, list[str]]:
    return parse_qs(urlencode({**FORM, **changes}, doseq=True), keep_blank_values=True)


@pytest.fixture
def site(tmp_path):
    kicks = []
    dashboard = Dashboard(
        JobStore(tmp_path / "jobs.sqlite"), kick=lambda: kicks.append(1), now=lambda: T0
    )
    dashboard.kicks = kicks
    return dashboard


@pytest.mark.parametrize(
    ("text", "rupiah"),
    [
        ("1500000000", 1_500_000_000),
        ("Rp 1.500.000.000", 1_500_000_000),
        ("850 juta", 850_000_000),
        ("1,5 miliar", 1_500_000_000),
        ("2 M", 2_000_000_000),
        ("cheap", None),
        ("", None),
    ],
)
def test_parse_budget(text, rupiah):
    assert parse_budget(text) == rupiah


def test_define_a_job_maps_the_area_and_redirects(site):
    response = site.handle("POST", "/jobs", _form())
    assert response.status == 303 and response.headers["Location"] == "/jobs/1"

    job = site.store.get_job(1)
    assert job.brief.area == "Bintaro" and job.area_text == "bintaro jaya"
    assert job.brief.budget_rp == 1_500_000_000 and job.brief.bedrooms == 3
    assert job.portals == ["rumah123", "99co"] and job.daily_time == "06:30"

    page = site.handle("GET", "/jobs/1").body
    assert "06:30 WIB" in page and "No Run yet" in page
    assert "Bintaro" in site.handle("GET", "/").body


def test_bad_form_is_shown_again_with_errors(site):
    response = site.handle(
        "POST", "/jobs", _form(budget="lots", portals=["evil.example"], daily_time="")
    )
    assert response.status == 422
    assert "Type the budget" in response.body and "Pick at least one Portal" in response.body
    assert 'value="bintaro jaya"' in response.body
    assert site.store.list_jobs() == []


def test_typed_text_is_escaped(site):
    site.handle("POST", "/jobs", _form(area="<script>alert(1)</script>"))
    page = site.handle("GET", "/jobs/1").body
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "cannot draw Comps" in page


def test_changing_portals_or_time_edits_the_job_in_place(site):
    site.handle("POST", "/jobs", _form())
    response = site.handle("POST", "/jobs/1", _form(portals=["pinhome"], daily_time="21:15"))
    assert response.headers["Location"] == "/jobs/1"
    job = site.store.get_job(1)
    assert job.portals == ["pinhome"] and job.daily_time == "21:15"
    assert len(site.store.list_jobs()) == 1


def test_brief_change_warns_then_makes_a_new_job(site):
    site.handle("POST", "/jobs", _form())
    warning = site.handle("POST", "/jobs/1", _form(budget="2 miliar"))
    assert warning.status == 200 and "makes a new Job" in warning.body
    assert len(site.store.list_jobs()) == 1

    response = site.handle("POST", "/jobs/1", _form(budget="2 miliar", confirm="1"))
    assert response.headers["Location"] == "/jobs/2"
    old, new = site.store.get_job(1), site.store.get_job(2)
    assert not old.active and old.brief.budget_rp == 1_500_000_000
    assert new.active and new.replaces == 1 and new.brief.budget_rp == 2_000_000_000
    assert "a newer Job" in site.handle("GET", "/jobs/1").body


def test_run_now_queues_one_run_and_kicks_a_tick(site):
    site.handle("POST", "/jobs", _form())
    assert site.handle("POST", "/jobs/1/run").headers["Location"] == "/jobs/1"
    assert site.kicks == [1] and site.store.queued_count() == 1
    assert "notice=busy" in site.handle("POST", "/jobs/1/run").headers["Location"]
    assert site.store.queued_count() == 1
    page = site.handle("GET", "/jobs/1").body
    assert "waiting to start" in page and 'http-equiv="refresh"' in page


def test_run_now_has_a_daily_limit(site, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_RUN_NOW_PER_DAY", 1)
    site.handle("POST", "/jobs", _form())
    site.handle("POST", "/jobs/1/run")
    site.store.finish(site.store.claim_next(T0).id, T0, error="x")
    assert "notice=limit" in site.handle("POST", "/jobs/1/run").headers["Location"]


def test_active_job_limit(site, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_ACTIVE_JOBS", 1)
    site.handle("POST", "/jobs", _form())
    assert site.handle("POST", "/jobs", _form()).status == 422
    site.handle("POST", "/jobs/1/active", {"active": ["0"]})
    assert not site.store.get_job(1).active
    assert site.handle("POST", "/jobs", _form()).status == 303


def test_job_page_shows_the_listing_list_and_no_page_text(site):
    job = site.store.add_job(a_job())
    run_id = site.store.enqueue(job.id, RunTrigger.NOW, T0)
    site.store.claim_next(T0)
    confirmed = [a_record(1, 1_000_000_000), a_record(2, 1_050_000_000), a_record(3, 700_000_000)]
    held = [a_record(8, 1, status=Status.QUARANTINED, status_reason="price does not match the page")]
    found = build_listing_list(job, final_state(confirmed, held), market_price=market_price, value=value)
    site.store.finish(run_id, T0, listing_list=found)

    page = site.handle("GET", "/jobs/1").body
    assert "Below Market" in page and "Rp 700.000.000" in page
    assert "Market Price from 3 Comps" in page
    assert "price does not match the page" in page
    assert "Pak Agen" not in page and "0812" not in page
    assert site.handle("GET", "/jobs/1?run=1").status == 200


@pytest.mark.parametrize(
    "target", ["/nope", "/jobs/99", "/jobs/99/edit", "/data/snapshots/x.html", "/jobs/abc"]
)
def test_unknown_addresses_are_not_found(site, target):
    assert site.handle("GET", target).status == 404


def test_other_methods_are_refused(site):
    assert site.handle("DELETE", "/jobs/1").status == 405
