from dealscout.collect.duplicates import mark_duplicates
from dealscout.domain import ListingRecord, PropertyType, Readiness


def _house(url: str, portal: str = "rumah123", listing_id: str | None = None, **overrides) -> ListingRecord:
    values = {
        "url": url,
        "portal": portal,
        "listing_id": listing_id,
        "price_rp": 875_000_000,
        "land_m2": 55.0,
        "building_m2": 60.0,
        "bedrooms": 2,
        "bathrooms": 2,
        "area": "Bintaro",
        "property_type": PropertyType.HOUSE,
        "readiness": Readiness.READY,
    } | overrides
    return ListingRecord(**values)


def test_same_house_on_a_second_url_points_at_the_first():
    first = _house("https://www.rumah123.com/a")
    second = _house("https://www.99.co/id/properti/b", portal="99co")
    mark_duplicates([first, second])
    assert first.duplicate_of is None
    assert second.duplicate_of == first.url


def test_same_listing_id_on_one_portal_is_a_duplicate():
    first = _house("https://www.rumah123.com/a", listing_id="hos1", land_m2=None)
    second = _house("https://www.rumah123.com/b", listing_id="hos1", land_m2=None, price_rp=900_000_000)
    mark_duplicates([first, second])
    assert second.duplicate_of == first.url


def test_different_houses_are_not_duplicates():
    a = _house("https://www.rumah123.com/a", land_m2=55)
    b = _house("https://www.rumah123.com/b", land_m2=80)
    mark_duplicates([a, b])
    assert a.duplicate_of is None
    assert b.duplicate_of is None


def test_later_copies_all_point_at_the_first_url():
    first = _house("https://www.rumah123.com/a")
    second = _house("https://www.99.co/id/properti/b", portal="99co")
    third = _house("https://www.pinhome.id/c", portal="pinhome")
    mark_duplicates([first, second, third])
    assert second.duplicate_of == first.url
    assert third.duplicate_of == first.url
