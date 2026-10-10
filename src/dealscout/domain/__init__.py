"""Contracts: the types every lane exchanges. Terms follow CONTEXT.md."""

from dealscout.domain.areas import AREAS, normalize_area
from dealscout.domain.brief import Brief
from dealscout.domain.job import (
    JOB_PORTALS,
    Job,
    JobRun,
    ListingList,
    ListingRow,
    JobRunState,
    RunTrigger,
)
from dealscout.domain.listing import (
    REQUIRED_FIELDS,
    CheckFailure,
    Disagreement,
    FieldSource,
    Listing,
    ListingRecord,
    PropertyType,
    Readiness,
    Snapshot,
    Status,
)
from dealscout.domain.valuation import Deal, MarketPrice, Shortlist, Valuation, ValuationTier

__all__ = [
    "AREAS",
    "REQUIRED_FIELDS",
    "Brief",
    "CheckFailure",
    "Deal",
    "Disagreement",
    "FieldSource",
    "JOB_PORTALS",
    "Job",
    "JobRun",
    "Listing",
    "ListingList",
    "ListingRecord",
    "ListingRow",
    "MarketPrice",
    "PropertyType",
    "Readiness",
    "JobRunState",
    "RunTrigger",
    "Shortlist",
    "Snapshot",
    "Status",
    "Valuation",
    "ValuationTier",
    "normalize_area",
]
