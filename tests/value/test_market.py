from dealscout.domain import Readiness, Status
from dealscout.value.market import market_price

from tests.value.helpers import make_confirmed


def _comps(n: int, area: str = "Bintaro"):
    return [
        make_confirmed(
            url=f"https://example.test/{area.lower()}-{i}",
            price_rp=1_200_000_000 + i * 10_000_000,
            land_m2=100,
            building_m2=80,
            area=area,
        )
        for i in range(n)
    ]


def test_three_confirmed_in_the_area_yield_a_market_price():
    rows = _comps(3)
    market = market_price("Bintaro", rows)
    assert market is not None
    assert market.area == "Bintaro"
    assert market.comp_count == 3
    assert market.median_rp_per_land_m2 == 12_100_000
    assert market.median_rp_per_building_m2 == 15_125_000
    assert market.comp_urls == [row.url for row in rows]


def test_fewer_than_three_comps_returns_none():
    assert market_price("Bintaro", _comps(2)) is None
    assert market_price("Bintaro", []) is None


def test_other_area_and_not_confirmed_are_not_comps():
    rows = _comps(3)
    rows[0] = make_confirmed(url="https://example.test/depok", area="Depok")
    rows[1] = make_confirmed(url="https://example.test/open", status=None)
    assert market_price("Bintaro", rows) is None


def test_indent_listing_is_not_a_comp():
    rows = _comps(3)
    rows[0] = make_confirmed(url="https://example.test/indent", readiness=Readiness.INDENT)
    assert market_price("Bintaro", rows) is None
    rows.append(make_confirmed(url="https://example.test/ready-3"))
    market = market_price("Bintaro", rows)
    assert market is not None
    assert market.comp_count == 3
    assert "https://example.test/indent" not in market.comp_urls
