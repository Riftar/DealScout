from enum import StrEnum

from pydantic import BaseModel, Field

from dealscout.domain.brief import Brief
from dealscout.domain.listing import ListingRecord


class ValuationTier(StrEnum):
    BELOW_MARKET = "below_market"
    AT_MARKET = "at_market"
    ABOVE_MARKET = "above_market"


class MarketPrice(BaseModel):
    """The going asking price in one Area, from Comps. Asking prices, not sale prices."""

    area: str
    comp_count: int = Field(ge=0)
    median_rp_per_land_m2: float
    median_rp_per_building_m2: float
    comp_urls: list[str] = Field(default_factory=list)


class Valuation(BaseModel):
    """One Confirmed Listing Record against the Market Price of its Area."""

    url: str
    expected_price_rp: int
    ratio: float  # asking price / expected price
    tier: ValuationTier
    land_ratio: float
    building_ratio: float
    split: bool = False  # land and building point to different tiers
    market: MarketPrice


class Deal(BaseModel):
    """A Confirmed Listing that fits the Brief and is Below Market."""

    record: ListingRecord
    valuation: Valuation
    rank: int | None = None
    soft_misses: list[str] = Field(default_factory=list)


class Shortlist(BaseModel):
    """What one Run hands back for a Brief."""

    brief: Brief
    deals: list[Deal] = Field(default_factory=list)
    considered: int = 0
    confirmed: int = 0
    quarantined: int = 0
    unreachable: int = 0
