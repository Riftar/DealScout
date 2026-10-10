from dealscout.domain import Brief, MarketPrice, Status, ValuationTier
from dealscout.value.valuation import shortlist, value

from tests.value.helpers import comps, confirmed


def _market(**overrides) -> MarketPrice:
    data = dict(
        area="Bintaro",
        comp_count=3,
        median_rp_per_land_m2=10_000_000,
        median_rp_per_building_m2=12_500_000,
        comp_urls=["https://example.test/1", "https://example.test/2", "https://example.test/3"],
    )
    data.update(overrides)
    return MarketPrice(**data)


def test_below_market_when_ratio_under_0_90():
    record = confirmed(price_rp=800_000_000, land_m2=100, building_m2=80)
    valuation = value(record, _market())
    assert valuation.expected_price_rp == 1_000_000_000
    assert valuation.ratio == 0.8
    assert valuation.tier is ValuationTier.BELOW_MARKET
    assert valuation.split is False


def test_at_market_between_thresholds():
    record = confirmed(price_rp=1_000_000_000, land_m2=100, building_m2=80)
    assert value(record, _market()).tier is ValuationTier.AT_MARKET
    assert value(confirmed(price_rp=900_000_000), _market()).tier is ValuationTier.AT_MARKET
    assert value(confirmed(price_rp=1_100_000_000), _market()).tier is ValuationTier.AT_MARKET


def test_above_market_when_ratio_over_1_10():
    record = confirmed(price_rp=1_200_000_000, land_m2=100, building_m2=80)
    assert value(record, _market()).tier is ValuationTier.ABOVE_MARKET


def test_split_when_land_and_building_tiers_differ():
    priced = _market(median_rp_per_land_m2=20_000_000, median_rp_per_building_m2=6_250_000)
    record = confirmed(price_rp=1_000_000_000, land_m2=100, building_m2=80)
    valuation = value(record, priced)
    assert valuation.split is True
    assert valuation.tier is ValuationTier.BELOW_MARKET
    assert valuation.land_ratio < 0.90
    assert valuation.building_ratio > 1.10


def test_deal_is_confirmed_in_brief_and_below_market():
    records = [
        *comps(1_000_000_000, 1_200_000_000, 800_000_000),
        confirmed(url="https://example.test/deal", price_rp=700_000_000),
    ]
    brief = Brief(area="Bintaro", budget_rp=1_500_000_000, land_m2=100, building_m2=80, bedrooms=3)
    result = shortlist(brief, records)
    assert result.deals
    assert all(deal.record.status is Status.CONFIRMED for deal in result.deals)
    assert all(deal.record.area == "Bintaro" for deal in result.deals)
    assert all(deal.record.price_rp <= brief.price_ceiling_rp for deal in result.deals)
    assert all(deal.valuation.tier is ValuationTier.BELOW_MARKET for deal in result.deals)
    assert [deal.rank for deal in result.deals] == list(range(1, len(result.deals) + 1))
    assert result.deals[0].valuation.ratio <= result.deals[-1].valuation.ratio


def test_over_ceiling_is_not_a_deal():
    records = comps(800_000_000, 900_000_000, 1_000_000_000)
    brief = Brief(area="Bintaro", budget_rp=500_000_000, headroom=0.05)
    assert shortlist(brief, records).deals == []


def test_other_area_is_not_a_deal():
    records = [
        *comps(800_000_000, 900_000_000, 1_000_000_000),
        confirmed(url="https://example.test/depok", area="Depok", price_rp=400_000_000),
    ]
    brief = Brief(area="Bintaro", budget_rp=1_500_000_000)
    urls = {deal.record.url for deal in shortlist(brief, records).deals}
    assert "https://example.test/depok" not in urls


def test_not_confirmed_is_not_a_deal():
    records = [
        *comps(1_000_000_000, 1_200_000_000, 800_000_000),
        confirmed(url="https://example.test/q", price_rp=500_000_000, status=Status.QUARANTINED),
    ]
    brief = Brief(area="Bintaro", budget_rp=1_500_000_000)
    urls = {deal.record.url for deal in shortlist(brief, records).deals}
    assert "https://example.test/q" not in urls


def test_soft_miss_on_size_and_bedrooms_is_listed_and_kept():
    records = [
        *comps(1_000_000_000, 1_200_000_000, 800_000_000),
        confirmed(
            url="https://example.test/soft",
            price_rp=600_000_000,
            land_m2=160,
            building_m2=130,
            bedrooms=1,
        ),
    ]
    brief = Brief(area="Bintaro", budget_rp=1_500_000_000, land_m2=100, building_m2=80, bedrooms=3)
    result = shortlist(brief, records)
    soft = next(deal for deal in result.deals if deal.record.url.endswith("/soft"))
    assert "land_m2" in soft.soft_misses
    assert "building_m2" in soft.soft_misses
    assert "bedrooms" in soft.soft_misses


def test_at_market_is_not_a_deal():
    records = comps(1_000_000_000, 1_000_000_000, 1_000_000_000)
    brief = Brief(area="Bintaro", budget_rp=2_000_000_000)
    assert shortlist(brief, records).deals == []
