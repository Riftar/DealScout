from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from dealscout.collect.corpus import INCLUDED_PORTALS
from dealscout.domain import JOB_PORTALS, Brief, Job


def _job(**changes) -> Job:
    body = {
        "brief": Brief(area="Bintaro", budget_rp=900_000_000),
        "area_text": "bintaro jaya",
        "portals": ["99co", "rumah123"],
        "daily_time": "06:30",
        "created_at": datetime(2026, 10, 11, tzinfo=UTC),
    }
    body.update(changes)
    return Job(**body)


def test_job_portals_are_all_in_the_corpus():
    assert set(JOB_PORTALS) <= INCLUDED_PORTALS


def test_job_keeps_portals_in_list_order():
    assert _job().portals == ["rumah123", "99co"]


@pytest.mark.parametrize(
    "changes",
    [{"portals": []}, {"portals": ["example.com"]}, {"daily_time": "24:00"}, {"daily_time": "6am"}],
)
def test_job_rejects_unknown_portals_and_bad_times(changes):
    with pytest.raises(ValidationError):
        _job(**changes)


def test_unmapped_area_text_is_flagged():
    assert _job().area_mapped
    assert not _job(brief=Brief(area="Cinere", budget_rp=900_000_000), area_text="Cinere").area_mapped
