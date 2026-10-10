"""Market Price from Confirmed Comps in one Area."""

from __future__ import annotations

import statistics

from dealscout.domain import Brief, ListingRecord, MarketPrice, Readiness, Status


def _similar_size(brief: Brief | None, record: ListingRecord) -> bool:
    if brief is None:
        return True
    if brief.land_m2 and record.land_m2:
        if abs(record.land_m2 - brief.land_m2) / brief.land_m2 > brief.soft_tolerance:
            return False
    if brief.building_m2 and record.building_m2:
        if abs(record.building_m2 - brief.building_m2) / brief.building_m2 > brief.soft_tolerance:
            return False
    return True


def market_price(
    area: str, confirmed: list[ListingRecord], brief: Brief | None = None
) -> MarketPrice | None:
    """Median asking Rp per m2 of land and of building. Fewer than three Comps returns None."""
    comps = [
        record
        for record in confirmed
        if record.area == area
        and record.status is Status.CONFIRMED
        and record.readiness is not Readiness.INDENT
        and not record.duplicate_of
        and record.price_per_land_m2 is not None
        and record.price_per_building_m2 is not None
        and _similar_size(brief, record)
    ]
    if len(comps) < 3:
        return None
    return MarketPrice(
        area=area,
        comp_count=len(comps),
        median_rp_per_land_m2=float(statistics.median(c.price_per_land_m2 for c in comps)),
        median_rp_per_building_m2=float(statistics.median(c.price_per_building_m2 for c in comps)),
        comp_urls=[c.url for c in comps],
    )
