from dealscout.domain import Disagreement, FieldSource, Status
from dealscout.verify.arbiter import arbitrate
from dealscout.verify.verifier import verify

from tests.verify.helpers import FakeModel, make_record, page_html, verifier_payload


def test_no_failures_and_no_disagreement_is_confirmed():
    record = make_record()
    html = page_html()
    settled = arbitrate(record, [], html, FakeModel({"quote": "unused"}))
    assert settled.status is Status.CONFIRMED
    assert settled.status_reason is None


def test_arbiter_settles_from_a_page_quote_and_confirms():
    record = make_record(building_m2=60, evidence={"building_m2": "Luas bangunan 60 m2"})
    html = page_html(building=62)
    disagreement = Disagreement(field="building_m2", scout_value="60", verifier_value="62")
    model = FakeModel({"quote": "Luas bangunan 62 m2", "value": "62", "cannot_settle": False})
    settled = arbitrate(record, [disagreement], html, model)
    assert settled.status is Status.CONFIRMED
    assert settled.building_m2 == 62
    assert settled.sources["building_m2"] is FieldSource.ARBITER
    assert settled.evidence["building_m2"] == "Luas bangunan 62 m2"
    assert disagreement.resolved_value == "62"
    assert disagreement.resolved_by is FieldSource.ARBITER
    assert "Scout value: 60" in model.prompts[0]
    assert "Verifier value: 62" in model.prompts[0]


def test_arbiter_quarantines_when_the_quote_is_not_on_the_page():
    record = make_record(building_m2=60, evidence={"building_m2": "Luas bangunan 60 m2"})
    html = page_html(building=62)
    disagreement = Disagreement(field="building_m2", scout_value="60", verifier_value="62")
    model = FakeModel({"quote": "this quote is invented", "value": "62", "cannot_settle": False})
    settled = arbitrate(record, [disagreement], html, model)
    assert settled.status is Status.QUARANTINED
    assert disagreement.resolved_value is None
    assert settled.building_m2 == 60


def test_arbiter_quarantines_when_it_cannot_settle():
    record = make_record(building_m2=60, evidence={"building_m2": "Luas bangunan 60 m2"})
    html = page_html(building=62)
    disagreement = Disagreement(field="building_m2", scout_value="60", verifier_value="62")
    model = FakeModel({"quote": None, "value": None, "cannot_settle": True})
    settled = arbitrate(record, [disagreement], html, model)
    assert settled.status is Status.QUARANTINED
    assert "building_m2" in (settled.status_reason or "")


def test_check_failure_without_disagreement_is_quarantined():
    record = make_record(bedrooms=89, evidence={"bedrooms": "Kamar tidur 89"})
    settled = arbitrate(record, [], page_html(bedrooms=89), FakeModel({}))
    assert settled.status is Status.QUARANTINED
    assert "89" in (settled.status_reason or "")


def test_verifier_then_arbiter_confirms_a_matching_page():
    record = make_record()
    html = page_html()
    disagreements = verify(record, html, FakeModel(verifier_payload(record)))
    settled = arbitrate(record, disagreements, html, FakeModel({}))
    assert disagreements == []
    assert settled.status is Status.CONFIRMED
