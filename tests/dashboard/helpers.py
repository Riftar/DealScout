from __future__ import annotations

from datetime import UTC, datetime

from dealscout.domain import Brief, Job, ListingRecord, PropertyType, Readiness, Status

T0 = datetime(2026, 10, 11, 1, 0, tzinfo=UTC)  # 08:00 WIB


def a_job(**changes) -> Job:
    body = {
        "brief": Brief(area="Bintaro", budget_rp=1_500_000_000),
        "area_text": "bintaro",
        "portals": ["rumah123", "99co"],
        "daily_time": "06:00",
        "created_at": T0,
    }
    body.update(changes)
    return Job(**body)


def a_record(n: int, price: int, *, land: float = 100, building: float = 80, **changes) -> ListingRecord:
    body = {
        "url": f"https://www.rumah123.com/properti/{n}",
        "portal": "rumah123",
        "listing_id": f"hos{n}",
        "price_rp": price,
        "land_m2": land,
        "building_m2": building,
        "bedrooms": 3,
        "bathrooms": 2,
        "area": "Bintaro",
        "property_type": PropertyType.HOUSE,
        "readiness": Readiness.READY,
        "title": f"Rumah {n} hubungi Pak Agen 0812-3456-7890",
        "status": Status.CONFIRMED,
    }
    body.update(changes)
    return ListingRecord(**body)


def final_state(confirmed=(), quarantined=(), unreachable=()) -> dict:
    return {
        "confirmed": [r.model_dump(mode="json") for r in confirmed],
        "quarantined": [r.model_dump(mode="json") for r in quarantined],
        "unreachable": [r.model_dump(mode="json") for r in unreachable],
    }
