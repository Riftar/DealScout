"""Each Extraction Check has a record that trips it and one that passes."""

from dealscout.domain import FieldSource, PropertyType
from dealscout.verify.checks import run_checks

from tests.verify.helpers import complete_record


def _names(record) -> list[str]:
    return [failure.check for failure in run_checks(record)]


def test_required_field_missing_trips():
    record = complete_record(land_m2=None)
    assert "required_missing" in _names(record)
    missing = [failure for failure in run_checks(record) if failure.check == "required_missing"]
    assert missing[0].field == "land_m2"


def test_required_fields_present_passes():
    assert "required_missing" not in _names(complete_record())


def test_bedrooms_above_20_trips():
    assert "bedrooms_high" in _names(complete_record(bedrooms=21))


def test_bedrooms_within_20_passes():
    assert "bedrooms_high" not in _names(complete_record(bedrooms=20))


def test_bathrooms_above_20_trips():
    assert "bathrooms_high" in _names(complete_record(bathrooms=205))


def test_bathrooms_within_20_passes():
    assert "bathrooms_high" not in _names(complete_record(bathrooms=7))


def test_land_size_outside_range_trips():
    assert "size_range" in _names(complete_record(land_m2=10))
    assert "size_range" in _names(complete_record(land_m2=5_001))


def test_land_size_inside_range_passes():
    for size in (15, 100, 5_000):
        record = complete_record(land_m2=size)
        record.evidence["land_m2"] = f"Luas tanah {size:g} m2"
        failures = [f for f in run_checks(record) if f.field == "land_m2"]
        assert failures == []


def test_building_size_outside_range_trips():
    assert "size_range" in _names(complete_record(building_m2=14.9))
    assert "size_range" in _names(complete_record(building_m2=5_000.1))


def test_building_size_inside_range_passes():
    assert "size_range" not in _names(complete_record(building_m2=80))


def test_price_outside_range_trips():
    assert "price_range" in _names(complete_record(price_rp=99_999_999, evidence={"price_rp": "Rp 99999999"}))
    assert "price_range" in _names(
        complete_record(price_rp=100_000_000_001, evidence={"price_rp": "Rp 100000000001"})
    )


def test_price_inside_range_passes():
    low = complete_record(price_rp=100_000_000, evidence={"price_rp": "Rp 100.000.000"})
    high = complete_record(price_rp=100_000_000_000, evidence={"price_rp": "Rp 100000000000"})
    assert "price_range" not in _names(low)
    assert "price_range" not in _names(high)


def test_price_in_url_or_title_differs_over_15_percent_trips():
    record = complete_record(
        url="https://example.test/rumah-rp-270-juta-bintaro",
        price_rp=500_000_000,
        evidence={"price_rp": "Rp 500.000.000"},
    )
    assert "price_in_url_or_title" in _names(record)


def test_price_in_title_differs_over_15_percent_trips():
    record = complete_record(
        title="Dijual Rumah Bintaro Rp 165 Juta",
        price_rp=1_650_000_000,
        evidence={"price_rp": "Rp 1.650.000.000"},
    )
    assert "price_in_url_or_title" in _names(record)


def test_price_in_url_within_15_percent_passes():
    record = complete_record(
        url="https://example.test/rumah-bintaro-1miliar",
        price_rp=1_100_000_000,
        evidence={"price_rp": "Rp 1.100.000.000"},
    )
    assert "price_in_url_or_title" not in _names(record)


def test_property_type_not_house_trips():
    assert "not_house" in _names(complete_record(property_type=PropertyType.OTHER, evidence={"property_type": "kosan"}))


def test_property_type_house_passes():
    assert "not_house" not in _names(complete_record())


def test_structured_value_differs_from_advert_text_trips():
    record = complete_record(
        building_m2=60,
        sources={"building_m2": FieldSource.STRUCTURED},
        evidence={"building_m2": "Luas bangunan 62 m2"},
    )
    failures = [f for f in run_checks(record) if f.check == "evidence_differs"]
    assert failures
    assert failures[0].field == "building_m2"


def test_structured_value_matches_advert_text_passes():
    record = complete_record(
        building_m2=62,
        evidence={"building_m2": "Luas bangunan 62 m2"},
    )
    assert "evidence_differs" not in _names(record)


def test_complete_record_has_no_failures():
    assert run_checks(complete_record()) == []
