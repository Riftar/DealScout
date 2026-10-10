import json

from dealscout.domain import FieldSource, PropertyType, Readiness
from dealscout.extract.structured import read_structured

# Hand-written pages in the shape each Portal uses. No real advert is copied here.


def rumah123_page(**home_overrides) -> str:
    home = {
        "@type": ["SingleFamilyResidence", "Product"],
        "sku": "hos1",
        "description": "Land Area: 55 m2   Building Area: 60 m2",
        "address": {"addressLocality": "Bintaro, Tangerang Selatan"},
        "numberOfBedrooms": 2,
        "numberOfBathroomsTotal": 2,
        "floorSize": {"@type": "QuantitativeValue", "value": 60},
        "offers": {"price": "875000000", "priceCurrency": "IDR"},
    } | home_overrides
    graph = {"@graph": [{"@type": ["WebPage", "RealEstateListing"], "name": "A house", "mainEntity": home}]}
    return f'<html><script type="application/ld+json">{json.dumps(graph)}</script></html>'


def ninety_nine_page(**attribute_overrides) -> str:
    attributes = {
        "property_type": {"value": "rumah"},
        "market_type": {"value": "secondary"},
        "bedrooms": 2,
        "bathrooms": 2,
        "land_area": {"value": "57", "unit": "m2"},
        "builtup_area": {"value": "60", "unit": "m2"},
        "electricity": {"value": "0", "unit": "Watt"},
        "certificate": {"value": "PPJB"},
        "floors": 2,
        "year_built": 0,
    } | attribute_overrides
    data = {
        "id": "abc",
        "title": "Rumah di BSD",
        "description": "Luas Bangunan 62m2",
        "price": {"price": 1_100_000_000},
        "attributes": attributes,
        "location": {"city": {"name": "Tangerang Selatan"}, "district": {"name": "BSD"}},
    }
    state = {"props": {"pageProps": {"data": data}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(state)}</script></html>'


def test_rumah123_states_everything_but_land_and_readiness():
    record = read_structured(rumah123_page(), "https://www.rumah123.com/en/property/x-hos1/", "rumah123")
    assert record.price_rp == 875_000_000
    assert record.building_m2 == 60
    assert (record.bedrooms, record.bathrooms) == (2, 2)
    assert record.area == "Bintaro"
    assert record.property_type is PropertyType.HOUSE
    assert record.missing_required() == ["land_m2", "readiness"]
    assert record.sources["price_rp"] is FieldSource.STRUCTURED
    assert record.description == "Land Area: 55 m2 Building Area: 60 m2"


def test_rumah123_new_launch_is_indent():
    url = "https://www.rumah123.com/en/new-launch/property/depok/x/hos2/"
    assert read_structured(rumah123_page(), url, "rumah123").readiness is Readiness.INDENT


def test_99co_states_every_required_field():
    record = read_structured(ninety_nine_page(), "https://www.99.co/id/properti/x", "99co")
    assert record.missing_required() == []
    assert record.price_rp == 1_100_000_000
    assert (record.land_m2, record.building_m2) == (57, 60)
    assert record.area == "BSD/Serpong"
    assert record.readiness is Readiness.READY
    assert record.certificate == "PPJB"


def test_zero_means_not_stated():
    record = read_structured(ninety_nine_page(), "https://www.99.co/id/properti/x", "99co")
    assert record.electricity_w is None
    assert record.year_built is None
    assert "electricity_w" not in record.sources


def test_non_house_is_marked_other():
    page = ninety_nine_page(property_type={"value": "kost"})
    assert read_structured(page, "https://www.99.co/id/properti/x", "99co").property_type is PropertyType.OTHER


def test_page_without_structured_data_yields_an_empty_record():
    record = read_structured("<html><body>nothing</body></html>", "https://www.99.co/id/properti/x", "99co")
    assert len(record.missing_required()) == 8
