"""Hand-built Listing Records and a fake model for verify tests."""

from __future__ import annotations

import json
from types import SimpleNamespace

from dealscout.domain import FieldSource, ListingRecord, PropertyType, Readiness, Status


def make_record(**overrides) -> ListingRecord:
    data = dict(
        url="https://example.test/rumah-bintaro",
        portal="example",
        price_rp=875_000_000,
        land_m2=100.0,
        building_m2=80.0,
        bedrooms=3,
        bathrooms=2,
        area="Bintaro",
        property_type=PropertyType.HOUSE,
        readiness=Readiness.READY,
        title="Rumah Bintaro siap huni",
        description="Luas tanah 100 m2. Luas bangunan 80 m2. Kamar tidur 3. Kamar mandi 2.",
        sources={
            "price_rp": FieldSource.STRUCTURED,
            "land_m2": FieldSource.STRUCTURED,
            "building_m2": FieldSource.STRUCTURED,
            "bedrooms": FieldSource.STRUCTURED,
            "bathrooms": FieldSource.STRUCTURED,
            "area": FieldSource.STRUCTURED,
            "property_type": FieldSource.STRUCTURED,
            "readiness": FieldSource.STRUCTURED,
        },
        evidence={
            "price_rp": "Rp 875.000.000",
            "land_m2": "Luas tanah 100 m2",
            "building_m2": "Luas bangunan 80 m2",
            "bedrooms": "Kamar tidur 3",
            "bathrooms": "Kamar mandi 2",
        },
        status=None,
    )
    data.update(overrides)
    return ListingRecord(**data)


def page_html(
    *,
    price: int = 875_000_000,
    land: float = 100,
    building: float = 80,
    bedrooms: int = 3,
    bathrooms: int = 2,
    area: str = "Bintaro",
) -> str:
    return (
        "<html><body>"
        f"<h1>Rumah {area} siap huni</h1>"
        f"<p>Harga Rp {price}.</p>"
        f"<p>Luas tanah {land} m2. Luas bangunan {building} m2.</p>"
        f"<p>Kamar tidur {bedrooms}. Kamar mandi {bathrooms}.</p>"
        "</body></html>"
    )


class FakeModel:
    """LangChain-shaped stand-in: with_structured_output and invoke, no live LLM."""

    def __init__(self, payloads: dict | list[dict]):
        self._queue = payloads if isinstance(payloads, list) else [payloads]
        self.prompts: list[str] = []

    def _next(self):
        return self._queue.pop(0) if len(self._queue) > 1 else self._queue[0]

    def invoke(self, prompt, **_kwargs):
        text = prompt if isinstance(prompt, str) else str(prompt)
        self.prompts.append(text)
        item = self._next()
        content = json.dumps(item) if isinstance(item, dict) else item
        return SimpleNamespace(content=content)

    def with_structured_output(self, schema):
        outer = self

        class Bound:
            def invoke(self, prompt, **_kwargs):
                text = prompt if isinstance(prompt, str) else str(prompt)
                outer.prompts.append(text)
                item = outer._next()
                if isinstance(item, schema):
                    return item
                return schema.model_validate(item)

        return Bound()


def verifier_payload(record: ListingRecord, **overrides) -> dict:
    payload = {
        "price_rp": record.price_rp,
        "land_m2": record.land_m2,
        "building_m2": record.building_m2,
        "bedrooms": record.bedrooms,
        "bathrooms": record.bathrooms,
        "area": record.area,
        "property_type": record.property_type.value if record.property_type else None,
        "readiness": record.readiness.value if record.readiness else None,
    }
    payload.update(overrides)
    return payload


def confirmed(**overrides) -> ListingRecord:
    record = make_record(**overrides)
    record.status = Status.CONFIRMED
    return record


def complete_record(**overrides) -> ListingRecord:
    """Every required field set; used by Extraction Check tests."""
    evidence = overrides.pop("evidence", None)
    sources = overrides.pop("sources", None)
    record = make_record(**overrides)
    if evidence is not None:
        record.evidence.update(evidence)
    if sources is not None:
        record.sources.update(sources)
    return record
