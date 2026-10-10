"""Verifier: re-reads a Snapshot on the strong model, never the Scout's values."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from dealscout.domain import (
    REQUIRED_FIELDS,
    Disagreement,
    ListingRecord,
    PropertyType,
    Readiness,
    normalize_area,
)
from dealscout.verify.model import invoke_json, page_text
from dealscout.verify.util import MIN_PRICE_RP, as_whole_rupiah, prices_agree

_PROMPT = """Read this house listing page and extract the fields below.
Return one JSON object and nothing else. Use null when the page does not state a field.
Do not guess. price_rp is whole Rupiah (885 juta is 885000000, not 885).
land_m2 and building_m2 are square metres.
property_type must be "house" or "other". readiness must be "ready" or "indent" (siap huni is ready).

Fields: {fields}

URL: {url}

Page:
{page}
"""


class VerifierExtract(BaseModel):
    """What the Verifier read from the Snapshot. Omit a field that is unstated."""

    price_rp: int | None = None
    land_m2: float | None = None
    building_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    area: str | None = None
    property_type: str | None = None
    readiness: str | None = None


def _reply_to_extract(model: Any, prompt: str) -> VerifierExtract | None:
    bound = getattr(model, "with_structured_output", None)
    if bound is not None:
        try:
            result = bound(VerifierExtract).invoke(prompt)
            if isinstance(result, VerifierExtract):
                return result
            return VerifierExtract.model_validate(result)
        except (ValidationError, ValueError, TypeError):
            pass
    data = invoke_json(model, prompt)
    if data is None:
        return None
    return VerifierExtract.model_validate(data)


def _as_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, (PropertyType, Readiness)):
        return value.value
    return str(value)


def _canon(field: str, value: Any) -> Any:
    if value is None or value == "" or str(value).lower() in {"null", "none"}:
        return None
    if field == "area":
        text = str(value).strip()
        return (normalize_area(text) or text).casefold()
    if field == "property_type":
        text = str(value).lower()
        if any(word in text for word in ("kost", "kosan", "apartemen", "apartment", "ruko")):
            return PropertyType.OTHER.value
        if text in {"house", "rumah", "singlefamilyresidence"} or "house" in text:
            return PropertyType.HOUSE.value
        if text == "other":
            return PropertyType.OTHER.value
        return text
    if field == "readiness":
        text = str(value).lower()
        if any(word in text for word in ("indent", "new launch", "primer", "primary")):
            return Readiness.INDENT.value
        if any(word in text for word in ("siap huni", "ready", "seken", "sekunder", "secondary")):
            return Readiness.READY.value
        return text
    if field in {"price_rp", "bedrooms", "bathrooms", "land_m2", "building_m2"}:
        try:
            number = float(str(value).replace(",", "").replace("_", "").strip())
        except (TypeError, ValueError):
            return str(value).strip().lower()
        if field == "price_rp":
            whole = as_whole_rupiah(number)
            return whole if whole is not None else int(number)
        if field in {"bedrooms", "bathrooms"}:
            return int(number)
        return number
    return str(value).strip().lower()


def _same(field: str, left: Any, right: Any) -> bool:
    a, b = _canon(field, left), _canon(field, right)
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if field == "price_rp":
            return prices_agree(float(a), float(b))
        return abs(float(a) - float(b)) < 1e-6
    return a == b


def verify(record: ListingRecord, html: str, model=None) -> list[Disagreement]:
    """Compare the Verifier's page read with the Listing Record, in code."""
    if model is None or not (html or "").strip():
        return []
    prompt = _PROMPT.format(fields=", ".join(REQUIRED_FIELDS), url=record.url, page=page_text(html))
    extracted = _reply_to_extract(model, prompt)
    if extracted is None:
        return [
            Disagreement(
                field=name,
                scout_value=_as_str(getattr(record, name)),
                verifier_value=None,
                note="Verifier did not return a readable JSON object",
            )
            for name in REQUIRED_FIELDS
            if getattr(record, name) is not None
        ]

    disagreements: list[Disagreement] = []
    for name in REQUIRED_FIELDS:
        scout = getattr(record, name)
        verifier_raw = getattr(extracted, name)
        if name == "price_rp" and scout is not None and verifier_raw is not None:
            try:
                scout_n = float(scout)
                verifier_n = float(verifier_raw)
            except (TypeError, ValueError):
                scout_n = verifier_n = None
            if scout_n is not None and verifier_n is not None and prices_agree(scout_n, verifier_n):
                whole = as_whole_rupiah(scout_n, verifier_n)
                if whole is not None and (record.price_rp or 0) < MIN_PRICE_RP:
                    record.price_rp = whole
                continue
        if _same(name, scout, verifier_raw):
            continue
        disagreements.append(
            Disagreement(
                field=name,
                scout_value=_as_str(scout),
                verifier_value=_as_str(verifier_raw),
            )
        )
    return disagreements
