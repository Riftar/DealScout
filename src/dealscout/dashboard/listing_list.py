"""Turn a finished Run into the Listing list the Dashboard shows for a Job."""

from __future__ import annotations

import re
from collections.abc import Callable

from dealscout.domain import (
    Brief,
    Job,
    ListingList,
    ListingRecord,
    ListingRow,
    MarketPrice,
    Status,
    Valuation,
)

# Reasons are written by the Checks, but a quoted value could carry a phone number.
_PHONE = re.compile(r"(?:\+?62|0)[\s.-]?8(?:[\s.-]?\d){7,11}")
_REASON_LIMIT = 240


def _reason(text: str | None, fallback: str) -> str:
    cleaned = _PHONE.sub("[number removed]", text or "").strip()
    return cleaned[:_REASON_LIMIT] or fallback


def _row(record: ListingRecord, status: Status, reason: str | None = None) -> ListingRow:
    return ListingRow(
        url=record.url,
        portal=record.portal,
        listing_id=record.listing_id,
        status=status,
        reason=reason,
        price_rp=record.price_rp,
        land_m2=record.land_m2,
        building_m2=record.building_m2,
        bedrooms=record.bedrooms,
        bathrooms=record.bathrooms,
        area=record.area,
        readiness=record.readiness,
    )


def _in_area(job: Job, record: ListingRecord) -> bool:
    if job.area_mapped:
        return record.area == job.brief.area
    # An Area DealScout does not know: match the typed text against the Listing's location.
    typed = job.area_text.strip().lower()
    where = " ".join(part for part in (record.detail_location, record.title) if part).lower()
    return bool(typed) and typed in where


def _soft_misses(brief: Brief, record: ListingRecord) -> list[str]:
    misses = []
    for name, wanted, found in (
        ("land size", brief.land_m2, record.land_m2),
        ("building size", brief.building_m2, record.building_m2),
        ("bedrooms", brief.bedrooms, record.bedrooms),
    ):
        if wanted is None or found is None:
            continue
        if abs(found - wanted) / max(wanted, 1) > brief.soft_tolerance:
            misses.append(name)
    return misses


def build_listing_list(
    job: Job,
    final: dict,
    *,
    market_price: Callable[..., MarketPrice | None],
    value: Callable[[ListingRecord, MarketPrice], Valuation],
) -> ListingList:
    """Rows are Confirmed Listings in the Brief's Area at or under budget plus Headroom,
    best Valuation ratio first. Only fields DealScout confirmed are copied; no page text."""
    brief = job.brief
    confirmed = [ListingRecord.model_validate(row) for row in final.get("confirmed") or []]
    quarantined = [ListingRecord.model_validate(row) for row in final.get("quarantined") or []]
    unreachable = [ListingRecord.model_validate(row) for row in final.get("unreachable") or []]

    market = market_price(brief.area, confirmed, brief) if job.area_mapped else None
    unique = [record for record in confirmed if not record.duplicate_of]
    rows: list[ListingRow] = []
    for record in unique:
        if not _in_area(job, record) or record.price_rp is None:
            continue
        if record.price_rp > brief.price_ceiling_rp:
            continue
        row = _row(record, Status.CONFIRMED)
        row.over_budget = record.price_rp > brief.budget_rp
        row.soft_misses = _soft_misses(brief, record)
        if market is not None and record.land_m2 and record.building_m2:
            valuation = value(record, market)
            row.ratio = valuation.ratio
            row.tier = valuation.tier
            row.split = valuation.split
            row.expected_price_rp = valuation.expected_price_rp
        rows.append(row)
    rows.sort(key=lambda row: (row.ratio is None, row.ratio or 0.0, row.price_rp or 0))

    return ListingList(
        rows=rows,
        quarantined=[
            _row(r, Status.QUARANTINED, _reason(r.status_reason, "reason not recorded"))
            for r in quarantined
        ],
        unreachable=[
            _row(r, Status.UNREACHABLE, _reason(r.status_reason, "page could not be read"))
            for r in unreachable
        ],
        confirmed=len(confirmed),
        outside_brief=len(unique) - len(rows),
        duplicates=len(confirmed) - len(unique),
        comp_count=market.comp_count if market else 0,
        market_rp_per_land_m2=market.median_rp_per_land_m2 if market else None,
        market_rp_per_building_m2=market.median_rp_per_building_m2 if market else None,
    )
