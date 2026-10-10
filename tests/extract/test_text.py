from dealscout.domain import FieldSource, ListingRecord, Readiness
from dealscout.extract.structured import read_structured
from dealscout.extract.text import read_text
from tests.extract.test_structured import ninety_nine_page, rumah123_page


class FakeModel:
    """Returns a canned TextExtract. Not a live LLM."""

    def __init__(self, payload: dict):
        self.payload = payload
        self.prompts: list[str] = []

    def with_structured_output(self, schema):
        parent = self

        class Bound:
            def invoke(self, prompt):
                parent.prompts.append(prompt)
                return schema.model_validate(parent.payload)

        return Bound()


def test_fills_only_missing_required_fields_from_the_advert():
    record = read_structured(rumah123_page(), "https://www.rumah123.com/en/property/x-hos1/", "rumah123")
    assert record.missing_required() == ["land_m2", "readiness"]
    model = FakeModel(
        {
            "land_m2": {"value": "55", "quote": "Land Area: 55 m2"},
            "readiness": {"value": "ready", "quote": "siap huni"},
        }
    )
    record.description = "Land Area: 55 m2 Building Area: 60 m2. Rumah siap huni."
    filled = read_text(record, model)
    assert filled.land_m2 == 55
    assert filled.readiness is Readiness.READY
    assert filled.sources["land_m2"] is FieldSource.MODEL
    assert filled.sources["readiness"] is FieldSource.MODEL
    assert filled.evidence["land_m2"] == "Land Area: 55 m2"
    assert filled.evidence["readiness"] == "siap huni"
    assert filled.sources["price_rp"] is FieldSource.STRUCTURED
    assert filled.missing_required() == []


def test_records_text_evidence_when_structured_already_filled():
    record = read_structured(ninety_nine_page(), "https://www.99.co/id/properti/x", "99co")
    assert record.building_m2 == 60
    model = FakeModel({"building_m2": {"value": "62", "quote": "Luas Bangunan 62m2"}})
    filled = read_text(record, model)
    assert filled.building_m2 == 60
    assert filled.sources["building_m2"] is FieldSource.STRUCTURED
    assert filled.evidence["building_m2"] == "Luas Bangunan 62m2"


def test_unstated_field_stays_none():
    record = ListingRecord(
        url="https://example.test/a",
        portal="example",
        description="Rumah di Bintaro. Harga Rp 875 juta.",
    )
    filled = read_text(record, FakeModel({"price_rp": {"value": "875000000", "quote": "Harga Rp 875 juta."}}))
    assert filled.price_rp == 875_000_000
    assert filled.land_m2 is None
    assert filled.bedrooms is None
    assert "land_m2" not in filled.sources


def test_quote_not_in_the_advert_is_ignored():
    record = ListingRecord(
        url="https://example.test/a",
        portal="example",
        description="Rumah di Bintaro tanpa angka luas.",
    )
    filled = read_text(record, FakeModel({"land_m2": {"value": "90", "quote": "Luas tanah 90 m2"}}))
    assert filled.land_m2 is None
    assert filled.evidence == {}


def test_empty_description_or_missing_model_leaves_the_record():
    record = ListingRecord(url="https://example.test/a", portal="example", price_rp=1)
    assert read_text(record, FakeModel({})).price_rp == 1
    record.description = "Ada teks."
    assert read_text(record, None).price_rp == 1
