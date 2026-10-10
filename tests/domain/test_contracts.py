import pytest
from pydantic import ValidationError

from dealscout.domain import REQUIRED_FIELDS, Brief, ListingRecord, PropertyType, Readiness


def test_price_ceiling_adds_headroom_to_budget():
    brief = Brief(area="Bintaro", budget_rp=2_000_000_000)
    assert brief.price_ceiling_rp == 2_100_000_000


def test_headroom_is_capped_at_ten_percent():
    with pytest.raises(ValidationError):
        Brief(area="Bintaro", budget_rp=2_000_000_000, headroom=0.25)


def test_empty_record_is_missing_every_required_field():
    record = ListingRecord(url="https://example.test/a", portal="example")
    assert record.missing_required() == list(REQUIRED_FIELDS)


def test_complete_record_is_missing_nothing_and_prices_per_m2():
    record = ListingRecord(
        url="https://example.test/a",
        portal="example",
        price_rp=1_500_000_000,
        land_m2=100,
        building_m2=75,
        bedrooms=3,
        bathrooms=2,
        area="Bintaro",
        property_type=PropertyType.HOUSE,
        readiness=Readiness.READY,
    )
    assert record.missing_required() == []
    assert record.price_per_land_m2 == 15_000_000
    assert record.price_per_building_m2 == 20_000_000


def test_price_per_m2_is_unknown_when_size_is_unknown():
    record = ListingRecord(url="https://example.test/a", portal="example", price_rp=1_500_000_000)
    assert record.price_per_land_m2 is None
    assert record.price_per_building_m2 is None
