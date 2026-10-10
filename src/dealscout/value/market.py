"""Market Price from Confirmed Comps in one Area."""

from __future__ import annotations

import statistics

from dealscout.domain import ListingRecord, MarketPrice, Readiness, Status


def market_price(area: str, confirmed: list[ListingRecord]) -> MarketPrice | None:
    """Median asking Rp per m2 of land and of building. Fewer than three Comps returns None."""
    comps = [
        record
        for record in confirmed
        if record.area == area
        and record.status is Status.CONFIRMED
        and record.readiness is not Readiness.INDENT
        and record.price_per_land_m2 is not None
        and record.price_per_building_m2 is not None
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
