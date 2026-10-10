from dealscout.dashboard.listing_list import build_listing_list
from dealscout.domain import Brief, Status, ValuationTier
from dealscout.value.market import market_price
from dealscout.value.valuation import value
from tests.dashboard.helpers import a_job, a_record, final_state


def _build(job, final):
    return build_listing_list(job, final, market_price=market_price, value=value)


def test_rows_are_ranked_by_valuation_ratio():
    confirmed = [
        a_record(1, 1_000_000_000),
        a_record(2, 1_050_000_000),
        a_record(3, 700_000_000),
        a_record(4, 1_100_000_000),
    ]
    found = _build(a_job(), final_state(confirmed))

    assert [row.listing_id for row in found.rows] == ["hos3", "hos1", "hos2", "hos4"]
    assert found.rows[0].tier is ValuationTier.BELOW_MARKET and found.rows[0].is_deal
    assert found.rows[0].ratio < found.rows[1].ratio
    assert found.comp_count == 4 and found.market_rp_per_land_m2


def test_fewer_than_three_comps_gives_no_ratio():
    found = _build(a_job(), final_state([a_record(1, 900_000_000), a_record(2, 950_000_000)]))
    assert [row.ratio for row in found.rows] == [None, None]
    assert found.comp_count == 0


def test_brief_limits_headroom_and_duplicates():
    job = a_job(brief=Brief(area="Bintaro", budget_rp=1_000_000_000, bedrooms=5))
    confirmed = [
        a_record(1, 1_040_000_000),  # inside Headroom
        a_record(2, 1_060_000_000),  # above budget plus Headroom
        a_record(3, 900_000_000, area="Depok"),
        a_record(4, 900_000_000, duplicate_of="https://www.rumah123.com/properti/1"),
    ]
    found = _build(job, final_state(confirmed))

    assert [row.listing_id for row in found.rows] == ["hos1"]
    assert found.rows[0].over_budget
    assert found.rows[0].soft_misses == ["bedrooms"]
    assert (found.confirmed, found.outside_brief, found.duplicates) == (4, 2, 1)


def test_held_aside_listings_carry_a_reason_without_phone_numbers():
    quarantined = a_record(
        7, 1, status=Status.QUARANTINED, status_reason="price quoted as WA 0812-3456-7890, not a number"
    )
    unreachable = a_record(8, 1, status=Status.UNREACHABLE, status_reason=None)
    found = _build(a_job(), final_state([], [quarantined], [unreachable]))

    assert "0812" not in found.quarantined[0].reason
    assert "number removed" in found.quarantined[0].reason
    assert found.unreachable[0].reason == "page could not be read"


def test_listing_list_holds_no_page_text():
    found = _build(a_job(), final_state([a_record(n, 900_000_000 + n) for n in range(1, 5)]))
    assert "Pak Agen" not in found.model_dump_json()


def test_unmapped_area_matches_location_text_and_draws_no_comps():
    job = a_job(brief=Brief(area="Cinere", budget_rp=1_500_000_000), area_text="Cinere")
    confirmed = [
        a_record(n, 900_000_000, area="Depok", detail_location="Cinere, Depok") for n in range(1, 5)
    ]
    confirmed.append(a_record(9, 900_000_000, area="Depok", detail_location="Sawangan, Depok"))
    found = _build(job, final_state(confirmed))

    assert len(found.rows) == 4
    assert all(row.ratio is None for row in found.rows)
