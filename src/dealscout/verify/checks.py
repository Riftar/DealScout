"""Extraction Checks: in code, no model. Each failure is one CheckFailure."""

from __future__ import annotations

import re
from urllib.parse import unquote

from dealscout.domain import CheckFailure, FieldSource, ListingRecord, PropertyType

MIN_SIZE_M2 = 15.0
MAX_SIZE_M2 = 5_000.0
MIN_PRICE_RP = 100_000_000
MAX_PRICE_RP = 100_000_000_000
PRICE_TEXT_LIMIT = 0.15

_INT_FIELDS = {"price_rp", "bedrooms", "bathrooms", "floors", "electricity_w", "year_built"}
_SIZE_FIELDS = ("land_m2", "building_m2")
_EVIDENCE_FIELDS = ("price_rp", "land_m2", "building_m2", "bedrooms", "bathrooms")

_MULTIPLIERS = {
    "juta": 1_000_000,
    "million": 1_000_000,
    "miliar": 1_000_000_000,
    "milyar": 1_000_000_000,
    "billion": 1_000_000_000,
}

_UNIT_PRICE = re.compile(
    r"(?<![A-Za-z])(\d+(?:[.,]\d+)?)\s*-?\s*(miliar|milyar|juta|billion|million)s?\b",
    re.I,
)
_RP_PRICE = re.compile(
    r"(?:rp|idr)\.?\s*(\d{1,3}(?:[.\s]\d{3}){2,}|\d{8,12})",
    re.I,
)
_LEAKED_VALUE = re.compile(r"['\"]value['\"]\s*:\s*['\"]?(\d+(?:[.,]\d+)?)", re.I)
_FIRST_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")


def _to_float(raw: str) -> float:
    text = raw.strip().replace(" ", "")
    if text.count(".") > 1 and "," not in text:
        return float(text.replace(".", ""))
    if text.count(",") > 1 and "." not in text:
        return float(text.replace(",", ""))
    if "," in text and "." in text:
        if text.rfind(".") > text.rfind(","):
            return float(text.replace(",", ""))
        return float(text.replace(".", "").replace(",", "."))
    if "," in text:
        whole, _, frac = text.partition(",")
        if len(frac) <= 2:
            return float(text.replace(",", "."))
        return float(text.replace(",", ""))
    return float(text)


def prices_in_text(text: str) -> list[int]:
    """Asking prices written with Rp, juta or miliar. Bare digit ids are ignored."""
    found: list[int] = []
    for match in _UNIT_PRICE.finditer(text):
        amount = _to_float(match.group(1)) * _MULTIPLIERS[match.group(2).lower()]
        value = int(round(amount))
        if value > 0:
            found.append(value)
    for match in _RP_PRICE.finditer(text):
        value = int(round(_to_float(match.group(1))))
        if value > 0:
            found.append(value)
    return found


def number_in_evidence(quote: str, field: str) -> float | None:
    """The numeric value the advert text states for one field."""
    if field == "price_rp":
        found = prices_in_text(quote)
        if found:
            return float(found[0])
    leaked = _LEAKED_VALUE.search(quote)
    if leaked:
        return _to_float(leaked.group(1))
    cleaned = quote.replace("m²", " ").replace("m2", " ").replace("M2", " ")
    match = _FIRST_NUMBER.search(cleaned)
    if match:
        return _to_float(match.group(1))
    return None


def _numbers_differ(structured: float, text_value: float, field: str) -> bool:
    if field in _INT_FIELDS:
        return int(round(structured)) != int(round(text_value))
    return abs(structured - text_value) > 0.05


def _url_and_title_text(record: ListingRecord) -> str:
    parts: list[str] = []
    if record.url:
        parts.append(unquote(record.url).replace("-", " ").replace("_", " "))
    if record.title:
        parts.append(record.title)
    return " ".join(parts)


def run_checks(record: ListingRecord) -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    for field in record.missing_required():
        failures.append(CheckFailure(check="required_missing", field=field, detail=f"{field} is missing"))
    if record.bedrooms is not None and record.bedrooms > 20:
        failures.append(CheckFailure(check="bedrooms_high", field="bedrooms", detail=str(record.bedrooms)))
    if record.bathrooms is not None and record.bathrooms > 20:
        failures.append(CheckFailure(check="bathrooms_high", field="bathrooms", detail=str(record.bathrooms)))
    for field in _SIZE_FIELDS:
        size = getattr(record, field)
        if size is not None and not (MIN_SIZE_M2 <= size <= MAX_SIZE_M2):
            failures.append(CheckFailure(check="size_range", field=field, detail=str(size)))
    if record.price_rp is not None and not (MIN_PRICE_RP <= record.price_rp <= MAX_PRICE_RP):
        failures.append(
            CheckFailure(check="price_range", field="price_rp", detail=str(record.price_rp))
        )
    if record.price_rp is not None:
        recorded = record.price_rp
        for found in prices_in_text(_url_and_title_text(record)):
            if abs(found - recorded) / recorded > PRICE_TEXT_LIMIT:
                failures.append(
                    CheckFailure(
                        check="price_in_url_or_title",
                        field="price_rp",
                        detail=f"page text {found} vs recorded {recorded}",
                    )
                )
                break
    if record.property_type is not None and record.property_type is not PropertyType.HOUSE:
        failures.append(
            CheckFailure(check="not_house", field="property_type", detail=record.property_type.value)
        )
    for field in _EVIDENCE_FIELDS:
        if record.sources.get(field) is not FieldSource.STRUCTURED:
            continue
        quote = record.evidence.get(field)
        structured = getattr(record, field)
        if not quote or structured is None:
            continue
        text_value = number_in_evidence(quote, field)
        if text_value is None:
            continue
        if _numbers_differ(float(structured), text_value, field):
            failures.append(
                CheckFailure(
                    check="evidence_differs",
                    field=field,
                    detail=f"structured {structured} vs advert text {text_value}",
                )
            )
    return failures
