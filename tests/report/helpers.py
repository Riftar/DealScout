"""Hand-made Shortlist, Quarantined and Unreachable Listings for the report tests."""

from dealscout.domain import (
    Brief,
    Deal,
    FieldSource,
    ListingRecord,
    MarketPrice,
    PropertyType,
    Readiness,
    Status,
    Valuation,
    ValuationTier,
)
from dealscout.report.html import ReportShortlist

BRIEF = Brief(area="Bintaro", budget_rp=1_500_000_000, land_m2=100, building_m2=80, bedrooms=3)

COMP_URLS = [
    "https://example.test/comp/a",
    "https://example.test/comp/b",
    "https://example.test/comp/c",
]


def _market() -> MarketPrice:
    return MarketPrice(
        area="Bintaro",
        comp_count=3,
        median_rp_per_land_m2=10_000_000,
        median_rp_per_building_m2=12_000_000,
        comp_urls=list(COMP_URLS),
    )


def _record(
    url: str,
    *,
    price_rp: int,
    land_m2: float,
    building_m2: float,
    title: str,
    evidence: dict[str, str],
    status: Status = Status.CONFIRMED,
    status_reason: str | None = None,
    bedrooms: int = 3,
    bathrooms: int = 2,
) -> ListingRecord:
    sources = {field: FieldSource.STRUCTURED for field in evidence}
    return ListingRecord(
        url=url,
        portal="example",
        listing_id=url.rsplit("/", 1)[-1],
        price_rp=price_rp,
        land_m2=land_m2,
        building_m2=building_m2,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area="Bintaro",
        property_type=PropertyType.HOUSE,
        readiness=Readiness.READY,
        title=title,
        sources=sources,
        evidence=evidence,
        status=status,
        status_reason=status_reason,
    )


def deal_one() -> Deal:
    record = _record(
        "https://example.test/listings/bintaro-deal-1",
        price_rp=700_000_000,
        land_m2=100,
        building_m2=80,
        title='Rumah "siap huni" & dekat stasiun',
        evidence={
            "price_rp": "Rp 700.000.000",
            "land_m2": "Luas tanah: 100 m2",
            "building_m2": "Luas bangunan: 80 m2",
            "bedrooms": "Kamar tidur: 3",
            "bathrooms": "Kamar mandi: 2",
            "area": "Bintaro Jaya",
            "property_type": "rumah",
            "readiness": "siap huni",
        },
    )
    market = _market()
    expected = round((100 * market.median_rp_per_land_m2 + 80 * market.median_rp_per_building_m2) / 2)
    return Deal(
        record=record,
        valuation=Valuation(
            url=record.url,
            expected_price_rp=expected,
            ratio=record.price_rp / expected,
            tier=ValuationTier.BELOW_MARKET,
            land_ratio=record.price_rp / (100 * market.median_rp_per_land_m2),
            building_ratio=record.price_rp / (80 * market.median_rp_per_building_m2),
            split=False,
            market=market,
        ),
        rank=1,
    )


def deal_two() -> Deal:
    record = _record(
        "https://example.test/listings/bintaro-deal-2",
        price_rp=850_000_000,
        land_m2=140,
        building_m2=110,
        title="Rumah 4 KT Bintaro",
        bedrooms=4,
        evidence={
            "price_rp": "Harga Rp 850 juta",
            "land_m2": "LT 140 m2",
            "building_m2": "LB 110 m2",
            "bedrooms": "4 KT",
            "bathrooms": "2 KM",
            "area": "Bintaro",
            "property_type": "house",
            "readiness": "Ready",
        },
    )
    market = _market()
    expected = round((140 * market.median_rp_per_land_m2 + 110 * market.median_rp_per_building_m2) / 2)
    return Deal(
        record=record,
        valuation=Valuation(
            url=record.url,
            expected_price_rp=expected,
            ratio=record.price_rp / expected,
            tier=ValuationTier.BELOW_MARKET,
            land_ratio=record.price_rp / (140 * market.median_rp_per_land_m2),
            building_ratio=record.price_rp / (110 * market.median_rp_per_building_m2),
            split=False,
            market=market,
        ),
        rank=2,
        soft_misses=["land_m2", "bedrooms"],
    )


def quarantined_listing() -> ListingRecord:
    return ListingRecord(
        url="https://example.test/listings/bintaro-thin",
        portal="example",
        price_rp=500_000_000,
        area="Bintaro",
        property_type=PropertyType.HOUSE,
        readiness=Readiness.READY,
        status=Status.QUARANTINED,
        status_reason="land_m2 is missing",
        sources={"price_rp": FieldSource.MODEL},
        evidence={"price_rp": "Rp 500 juta"},
    )


def unreachable_listing() -> ListingRecord:
    return ListingRecord(
        url="https://www.olx.co.id/item/gone",
        portal="olx",
        status=Status.UNREACHABLE,
        status_reason="request failed: Timeout",
    )


def handmade_shortlist() -> ReportShortlist:
    """Hand-made Shortlist with held-aside Listings attached until the contract carries them."""
    return ReportShortlist(
        brief=BRIEF,
        deals=[deal_one(), deal_two()],
        considered=4,
        confirmed=2,
        quarantined=1,
        unreachable=1,
        quarantined_listings=[quarantined_listing()],
        unreachable_listings=[unreachable_listing()],
    )
