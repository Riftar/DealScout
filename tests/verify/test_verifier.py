from dealscout.domain import ListingRecord
from dealscout.verify.verifier import VerifierExtract, verify

from tests.verify.helpers import FakeModel, make_record, page_html, verifier_payload

HTML = page_html()


def test_matching_snapshot_read_has_no_disagreement():
    record = make_record()
    model = FakeModel(verifier_payload(record))
    assert verify(record, HTML, model) == []
    assert model.prompts
    assert "Scout" not in model.prompts[0]
    before_page = model.prompts[0].split("Page:", 1)[0]
    assert "875000000" not in before_page.replace(",", "").replace(".", "")


def test_verifier_never_sees_scout_price():
    record = make_record(price_rp=777_000_000, evidence={"price_rp": "Rp 777.000.000"})
    model = FakeModel(verifier_payload(record, price_rp=875_000_000))
    disagreements = verify(record, HTML, model)
    prompt = model.prompts[0]
    assert "777000000" not in prompt.replace(",", "").replace(".", "")
    assert "Harga Rp 875000000" in prompt.replace(".", "")
    assert any(item.field == "price_rp" for item in disagreements)
    price = next(item for item in disagreements if item.field == "price_rp")
    assert price.scout_value == "777000000"
    assert price.verifier_value == "875000000"


def test_juta_price_is_not_a_disagreement():
    record = make_record(price_rp=875_000_000)
    model = FakeModel(verifier_payload(record, price_rp=875))
    assert verify(record, HTML, model) == []


def test_building_size_disagreement():
    record = make_record(building_m2=60, evidence={"building_m2": "Luas bangunan 60 m2"})
    model = FakeModel(verifier_payload(record, building_m2=62))
    disagreements = verify(record, HTML, model)
    assert [item.field for item in disagreements] == ["building_m2"]
    assert disagreements[0].scout_value == "60"
    assert disagreements[0].verifier_value == "62"


def test_rumah_and_siap_huni_match_house_and_ready():
    record = make_record()
    model = FakeModel(
        verifier_payload(record, area="Bintaro Jaya", property_type="rumah", readiness="siap huni")
    )
    assert verify(record, HTML, model) == []


def test_no_model_returns_no_disagreement():
    assert verify(make_record(), HTML, model=None) == []


def test_empty_html_returns_no_disagreement():
    record = ListingRecord(url="https://example.test/a", portal="example")
    assert verify(record, "  ", FakeModel({})) == []


def test_verifier_extract_schema_exists():
    assert VerifierExtract(price_rp=1).price_rp == 1
