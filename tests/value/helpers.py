from dealscout.domain import FieldSource, ListingRecord, PropertyType, Readiness, Status


def make_confirmed(**overrides) -> ListingRecord:
    data = dict(
        url="https://example.test/rumah-bintaro",
        portal="example",
        price_rp=1_000_000_000,
        land_m2=100.0,
        building_m2=80.0,
        bedrooms=3,
        bathrooms=2,
        area="Bintaro",
        property_type=PropertyType.HOUSE,
        readiness=Readiness.READY,
        status=Status.CONFIRMED,
        sources={"price_rp": FieldSource.STRUCTURED},
    )
    data.update(overrides)
    return ListingRecord(**data)


def confirmed(**overrides) -> ListingRecord:
    return make_confirmed(**overrides)


def comps(*price_rps: int, area: str = "Bintaro") -> list[ListingRecord]:
    """Three or more Confirmed Comps with the given asking prices."""
    return [
        make_confirmed(
            url=f"https://example.test/comp-{i}",
            price_rp=price,
            land_m2=100.0,
            building_m2=80.0,
            area=area,
        )
        for i, price in enumerate(price_rps)
    ]
