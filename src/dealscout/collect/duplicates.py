"""Mark Listings that advertise the same house, pointing later ones at the first URL."""

from dealscout.domain import ListingRecord


def _listing_key(record: ListingRecord) -> tuple | None:
    if not record.listing_id:
        return None
    return ("id", record.portal, record.listing_id)


def _house_key(record: ListingRecord) -> tuple | None:
    if None in (
        record.area,
        record.land_m2,
        record.building_m2,
        record.bedrooms,
        record.bathrooms,
        record.price_rp,
    ):
        return None
    return (
        "house",
        record.area,
        round(record.land_m2),
        round(record.building_m2),
        record.bedrooms,
        record.bathrooms,
        record.price_rp,
    )


def mark_duplicates(records: list[ListingRecord]) -> list[ListingRecord]:
    """Set duplicate_of on later records of the same house to the first URL seen."""
    seen: dict[tuple, str] = {}
    for record in records:
        keys = [key for key in (_listing_key(record), _house_key(record)) if key]
        original = next((seen[key] for key in keys if key in seen), None)
        if original and original != record.url:
            record.duplicate_of = original
            winner = original
        else:
            winner = record.url
        for key in keys:
            seen.setdefault(key, winner)
    return records
