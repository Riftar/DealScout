"""Valuation against Market Price, and the Shortlist of Deals for a Brief."""

from __future__ import annotations

from dealscout.domain import (
    Brief,
    Deal,
    ListingRecord,
    MarketPrice,
    Shortlist,
    Status,
    Valuation,
    ValuationTier,
)
from dealscout.value.market import market_price


def _tier(ratio: float) -> ValuationTier:
    if ratio < 0.90:
        return ValuationTier.BELOW_MARKET
    if ratio > 1.10:
        return ValuationTier.ABOVE_MARKET
    return ValuationTier.AT_MARKET


def value(record: ListingRecord, market: MarketPrice) -> Valuation:
    """Expected price is the mean of the land estimate and the building estimate."""
    land_est = record.land_m2 * market.median_rp_per_land_m2
    building_est = record.building_m2 * market.median_rp_per_building_m2
    expected = round((land_est + building_est) / 2)
    ratio = record.price_rp / expected if expected else 1.0
    land_ratio = record.price_rp / land_est if land_est else 1.0
    building_ratio = record.price_rp / building_est if building_est else 1.0
    return Valuation(
        url=record.url,
        expected_price_rp=expected,
        ratio=ratio,
        tier=_tier(ratio),
        land_ratio=land_ratio,
        building_ratio=building_ratio,
        split=_tier(land_ratio) != _tier(building_ratio),
        market=market,
    )


def _soft_misses(brief: Brief, record: ListingRecord) -> list[str]:
    misses: list[str] = []
    if brief.land_m2 and record.land_m2:
        if abs(record.land_m2 - brief.land_m2) / brief.land_m2 > brief.soft_tolerance:
            misses.append("land_m2")
    if brief.building_m2 and record.building_m2:
        if abs(record.building_m2 - brief.building_m2) / brief.building_m2 > brief.soft_tolerance:
            misses.append("building_m2")
    if brief.bedrooms is not None and record.bedrooms is not None:
        if abs(record.bedrooms - brief.bedrooms) / max(brief.bedrooms, 1) > brief.soft_tolerance:
            misses.append("bedrooms")
    return misses


def shortlist(brief: Brief, confirmed: list[ListingRecord]) -> Shortlist:
    """Deals: Confirmed, Brief Area, price at or under the ceiling, Below Market.

    Soft misses on size and bedrooms are listed on the Deal and never drop it.
    """
    in_area = [
        record
        for record in confirmed
        if record.status is Status.CONFIRMED
        and record.area == brief.area
        and not record.duplicate_of
        and record.price_rp is not None
        and record.price_rp <= brief.price_ceiling_rp
        and record.land_m2
        and record.building_m2
    ]
    market = market_price(brief.area, confirmed, brief)
    deals: list[Deal] = []
    if market is not None:
        for record in in_area:
            valuation = value(record, market)
            if valuation.tier is not ValuationTier.BELOW_MARKET:
                continue
            deals.append(Deal(record=record, valuation=valuation, soft_misses=_soft_misses(brief, record)))
        deals.sort(key=lambda deal: deal.valuation.ratio)
        for rank, deal in enumerate(deals, start=1):
            deal.rank = rank
    confirmed_count = sum(1 for record in confirmed if record.status is Status.CONFIRMED)
    return Shortlist(
        brief=brief,
        deals=deals,
        considered=len(confirmed),
        confirmed=confirmed_count,
    )
