"""Stand-ins for lanes that have not merged yet. Real modules replace these via seams."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

from dealscout.domain import (
    Brief,
    CheckFailure,
    Deal,
    Disagreement,
    FieldSource,
    ListingRecord,
    MarketPrice,
    PropertyType,
    Readiness,
    Shortlist,
    Status,
    Valuation,
    ValuationTier,
)

_LAND = re.compile(r"(?:luas\s*tanah|land\s*area|lt)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:m2|m²)?", re.I)
_BUILDING = re.compile(
    r"(?:luas\s*bangunan|building\s*area|lb)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:m2|m²)?", re.I
)
_BEDROOMS = re.compile(r"(?:kamar\s*tidur|bedrooms?|kt)\s*[:=]?\s*(\d+)", re.I)
_BATHROOMS = re.compile(r"(?:kamar\s*mandi|bathrooms?|km)\s*[:=]?\s*(\d+)", re.I)


def read_text(record: ListingRecord, model=None) -> ListingRecord:
    """Fill missing required fields from advert text with simple patterns. Ignores model."""
    del model
    text = " ".join(part for part in (record.title, record.description) if part) or ""
    if not text:
        return record

    matches: dict[str, re.Match[str] | None] = {
        "land_m2": _LAND.search(text),
        "building_m2": _BUILDING.search(text),
        "bedrooms": _BEDROOMS.search(text),
        "bathrooms": _BATHROOMS.search(text),
    }
    for field, match in matches.items():
        if match is None:
            continue
        raw = match.group(1).replace(",", ".")
        value: float | int = int(raw) if field in {"bedrooms", "bathrooms"} else float(raw)
        quote = match.group(0)
        if field in record.missing_required():
            setattr(record, field, value)
            record.sources[field] = FieldSource.MODEL
            record.evidence[field] = quote
        else:
            # Structured already filled: still record what the text says for the Verifier.
            record.evidence.setdefault(field, quote)

    lower = text.lower()
    if "readiness" in record.missing_required():
        if "siap huni" in lower or "ready" in lower:
            record.readiness = Readiness.READY
            record.sources["readiness"] = FieldSource.MODEL
            record.evidence["readiness"] = "siap huni" if "siap huni" in lower else "ready"
        elif "indent" in lower or "new launch" in lower or "baru" in lower:
            record.readiness = Readiness.INDENT
            record.sources["readiness"] = FieldSource.MODEL
            record.evidence["readiness"] = "indent"

    if "property_type" in record.missing_required():
        if "kosan" in lower or "kost" in lower:
            record.property_type = PropertyType.OTHER
        else:
            record.property_type = PropertyType.HOUSE
        record.sources["property_type"] = FieldSource.MODEL
        record.evidence["property_type"] = record.property_type.value

    return record


def run_checks(record: ListingRecord) -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    for field in record.missing_required():
        failures.append(CheckFailure(check="required_missing", field=field, detail=f"{field} is missing"))
    if record.bedrooms is not None and record.bedrooms > 20:
        failures.append(CheckFailure(check="bedrooms_high", field="bedrooms", detail=str(record.bedrooms)))
    if record.bathrooms is not None and record.bathrooms > 20:
        failures.append(CheckFailure(check="bathrooms_high", field="bathrooms", detail=str(record.bathrooms)))
    for field in ("land_m2", "building_m2"):
        size = getattr(record, field)
        if size is not None and not (15 <= size <= 5_000):
            failures.append(CheckFailure(check="size_range", field=field, detail=str(size)))
    if record.price_rp is not None and not (100_000_000 <= record.price_rp <= 100_000_000_000):
        failures.append(CheckFailure(check="price_range", field="price_rp", detail=str(record.price_rp)))
    if record.property_type is not None and record.property_type is not PropertyType.HOUSE:
        failures.append(
            CheckFailure(check="not_house", field="property_type", detail=record.property_type.value)
        )
    return failures


def verify(record: ListingRecord, html: str, model=None) -> list[Disagreement]:
    """Fake Verifier: no Disagreements. Real lane replaces this."""
    del record, html, model
    return []


def arbitrate(
    record: ListingRecord, disagreements: list[Disagreement], html: str, model=None
) -> ListingRecord:
    """Confirm when clean; Quarantine when checks or open Disagreements remain."""
    del html, model
    open_ones = [d for d in disagreements if d.resolved_value is None]
    failures = run_checks(record)
    if failures or open_ones:
        reasons = [f.detail for f in failures] + [d.field for d in open_ones]
        record.status = Status.QUARANTINED
        record.status_reason = "; ".join(reasons) or "unresolved disagreement"
        return record
    record.status = Status.CONFIRMED
    record.status_reason = None
    return record


def market_price(area: str, confirmed: list[ListingRecord]) -> MarketPrice | None:
    comps = [
        r
        for r in confirmed
        if r.area == area
        and r.status is Status.CONFIRMED
        and r.price_per_land_m2 is not None
        and r.price_per_building_m2 is not None
    ]
    if len(comps) < 3:
        return None
    return MarketPrice(
        area=area,
        comp_count=len(comps),
        median_rp_per_land_m2=float(statistics.median(c.price_per_land_m2 for c in comps)),
        median_rp_per_building_m2=float(statistics.median(c.price_per_building_m2 for c in comps)),
        comp_urls=[c.url for c in comps],
    )


def _tier(ratio: float) -> ValuationTier:
    if ratio < 0.90:
        return ValuationTier.BELOW_MARKET
    if ratio > 1.10:
        return ValuationTier.ABOVE_MARKET
    return ValuationTier.AT_MARKET


def value(record: ListingRecord, market: MarketPrice) -> Valuation:
    land_est = record.land_m2 * market.median_rp_per_land_m2
    building_est = record.building_m2 * market.median_rp_per_building_m2
    expected = round((land_est + building_est) / 2)
    ratio = record.price_rp / expected if expected else 1.0
    land_ratio = record.price_rp / land_est if land_est else 1.0
    building_ratio = record.price_rp / building_est if building_est else 1.0
    land_tier = _tier(land_ratio)
    building_tier = _tier(building_ratio)
    return Valuation(
        url=record.url,
        expected_price_rp=expected,
        ratio=ratio,
        tier=_tier(ratio),
        land_ratio=land_ratio,
        building_ratio=building_ratio,
        split=land_tier != building_tier,
        market=market,
    )


def shortlist(brief: Brief, confirmed: list[ListingRecord]) -> Shortlist:
    in_area = [
        r
        for r in confirmed
        if r.status is Status.CONFIRMED
        and r.area == brief.area
        and r.price_rp is not None
        and r.price_rp <= brief.price_ceiling_rp
        and r.land_m2
        and r.building_m2
    ]
    market = market_price(brief.area, confirmed)
    deals: list[Deal] = []
    if market is not None:
        for record in in_area:
            valuation = value(record, market)
            if valuation.tier is not ValuationTier.BELOW_MARKET:
                continue
            soft: list[str] = []
            if brief.land_m2 and record.land_m2:
                if abs(record.land_m2 - brief.land_m2) / brief.land_m2 > brief.soft_tolerance:
                    soft.append("land_m2")
            if brief.building_m2 and record.building_m2:
                if abs(record.building_m2 - brief.building_m2) / brief.building_m2 > brief.soft_tolerance:
                    soft.append("building_m2")
            if brief.bedrooms is not None and record.bedrooms is not None:
                if abs(record.bedrooms - brief.bedrooms) / max(brief.bedrooms, 1) > brief.soft_tolerance:
                    soft.append("bedrooms")
            deals.append(Deal(record=record, valuation=valuation, soft_misses=soft))
        deals.sort(key=lambda d: d.valuation.ratio)
        for i, deal in enumerate(deals, start=1):
            deal.rank = i
    return Shortlist(
        brief=brief,
        deals=deals,
        considered=len(confirmed),
        confirmed=len(confirmed),
    )


def write_report(shortlist: Shortlist, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "shortlist.json"
    html_path = out_dir / "report.html"
    payload = shortlist.model_dump(mode="json")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rows = []
    for deal in shortlist.deals:
        rows.append(
            "<tr>"
            f"<td>{deal.rank}</td>"
            f"<td>{deal.record.url}</td>"
            f"<td>{deal.record.price_rp}</td>"
            f"<td>{deal.valuation.expected_price_rp}</td>"
            f"<td>{deal.valuation.ratio:.3f}</td>"
            "</tr>"
        )
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>DealScout Shortlist</title></head>"
        f"<body><h1>Shortlist: {shortlist.brief.area}</h1>"
        f"<p>confirmed={shortlist.confirmed} quarantined={shortlist.quarantined} "
        f"unreachable={shortlist.unreachable}</p>"
        "<table><thead><tr><th>rank</th><th>url</th><th>asking</th><th>expected</th>"
        "<th>ratio</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>",
        encoding="utf-8",
    )
    return html_path
