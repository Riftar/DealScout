"""A buyer's Job, its Runs, and the Listing list the Dashboard shows for one Run."""

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from dealscout.domain.areas import AREAS
from dealscout.domain.brief import Brief
from dealscout.domain.listing import Readiness, Status
from dealscout.domain.valuation import ValuationTier

# The Portals a buyer may pick on a Job, with the name shown on the Dashboard.
JOB_PORTALS: dict[str, str] = {
    "rumah123": "rumah123",
    "99co": "99.co",
    "pinhome": "Pinhome",
    "masuksini": "masuksini",
    "idrumah": "idrumah",
    "olx": "OLX",
}

_DAILY_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Job(BaseModel):
    """A buyer's saved hunt: one Brief, chosen Portals and a daily time in Asia/Jakarta."""

    id: int | None = None
    brief: Brief
    area_text: str  # what the buyer typed; brief.area is the canonical Area when it mapped
    portals: list[str] = Field(min_length=1)
    daily_time: str  # "HH:MM", Asia/Jakarta
    active: bool = True
    created_at: datetime
    replaces: int | None = None  # the Job this one was made from by a Brief change

    @field_validator("portals")
    @classmethod
    def _known_portals(cls, portals: list[str]) -> list[str]:
        unknown = [name for name in portals if name not in JOB_PORTALS]
        if unknown:
            raise ValueError(f"not a Portal a Job can use: {', '.join(unknown)}")
        return [name for name in JOB_PORTALS if name in portals]

    @field_validator("daily_time")
    @classmethod
    def _clock_time(cls, value: str) -> str:
        if not _DAILY_TIME.match(value):
            raise ValueError("daily time must be HH:MM")
        return value

    @property
    def area_mapped(self) -> bool:
        """Whether the typed Area mapped to a canonical one. Unmapped text cannot draw Comps."""
        return self.brief.area in AREAS


class RunTrigger(StrEnum):
    DAILY = "daily"
    NOW = "now"


class JobRunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class ListingRow(BaseModel):
    """One Listing on a Job's Listing list. Holds no text copied from the Listing's page."""

    url: str
    portal: str
    listing_id: str | None = None
    status: Status
    reason: str | None = None  # why it is Quarantined or Unreachable
    price_rp: int | None = None
    land_m2: float | None = None
    building_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    area: str | None = None
    readiness: Readiness | None = None
    over_budget: bool = False  # above the Brief's budget, inside Headroom
    soft_misses: list[str] = Field(default_factory=list)
    # Set only when the Listing has at least three Comps.
    ratio: float | None = None
    tier: ValuationTier | None = None
    split: bool = False
    expected_price_rp: int | None = None

    @property
    def is_deal(self) -> bool:
        return self.tier is ValuationTier.BELOW_MARKET


class ListingList(BaseModel):
    """What one Run found for a Job, as the Dashboard shows it."""

    rows: list[ListingRow] = Field(default_factory=list)  # Confirmed Listings that fit the Brief
    quarantined: list[ListingRow] = Field(default_factory=list)
    unreachable: list[ListingRow] = Field(default_factory=list)
    confirmed: int = 0
    outside_brief: int = 0  # Confirmed, but another Area or above budget plus Headroom
    duplicates: int = 0
    comp_count: int = 0
    market_rp_per_land_m2: float | None = None
    market_rp_per_building_m2: float | None = None


class JobRun(BaseModel):
    """One firing of a Job."""

    id: int
    job_id: int
    trigger: RunTrigger
    state: JobRunState
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    trace_id: str | None = None
    error: str | None = None
    listing_list: ListingList | None = None
