"""The Scout's model read of advert text, filling only required fields still missing."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ValidationError

from dealscout.domain import (
    REQUIRED_FIELDS,
    FieldSource,
    ListingRecord,
    PropertyType,
    Readiness,
    normalize_area,
)
from dealscout.extract.structured import parse_rupiah
from dealscout.verify.util import as_whole_rupiah

_SPACE = re.compile(r"\s+")


class Quoted(BaseModel):
    """One field as the advert states it, plus the exact words it was read from."""

    value: str | None = None
    quote: str | None = None


class TextExtract(BaseModel):
    """What the advert text states for each required field. Omit a field that is unstated."""

    price_rp: Quoted | None = None
    land_m2: Quoted | None = None
    building_m2: Quoted | None = None
    bedrooms: Quoted | None = None
    bathrooms: Quoted | None = None
    area: Quoted | None = None
    property_type: Quoted | None = None
    readiness: Quoted | None = None


_PROMPT = """You read Indonesian house listing adverts for DealScout.
Extract only what this advert text states for: price_rp, land_m2, building_m2, bedrooms, bathrooms, area, property_type, readiness.
For each field the text states, return an interpreted value and the exact words from the advert (quote).
If the text does not state a field, omit it. Do not guess.
property_type is house or other (kost, kosan, apartemen are other).
readiness is ready (siap huni, secondary) or indent (baru, new launch, primary).
price_rp is whole Rupiah. area is the neighbourhood name as written.
Quotes must be copied verbatim from the advert.
Reply with one JSON object only. No markdown, no commentary.
Each present field is {"value": "...", "quote": "..."}. Omit unstated fields.

Advert text:
{description}
"""


def _norm(text: str) -> str:
    return _SPACE.sub(" ", text).strip().lower()


def _quote_in_advert(quote: str | None, description: str) -> str | None:
    if not quote:
        return None
    if _norm(quote) not in _norm(description):
        return None
    return quote.strip()


def _as_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", value.replace(" ", ""))
    if not match:
        return None
    raw = match.group(1)
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        parsed = float(raw)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _as_int(value: str | None) -> int | None:
    number = _as_float(value)
    return int(number) if number is not None else None


def _as_property_type(value: str | None, quote: str | None) -> PropertyType | None:
    blob = f"{value or ''} {quote or ''}".lower()
    if any(word in blob for word in ("kost", "kosan", "apartemen", "apartment", "ruko", "other")):
        return PropertyType.OTHER
    if any(word in blob for word in ("rumah", "house")):
        return PropertyType.HOUSE
    return None


def _as_readiness(value: str | None, quote: str | None) -> Readiness | None:
    blob = f"{value or ''} {quote or ''}".lower()
    if any(word in blob for word in ("indent", "new launch", "primer", "primary")):
        return Readiness.INDENT
    if any(word in blob for word in ("siap huni", "ready", "seken", "sekunder", "secondary")):
        return Readiness.READY
    return None


def _convert(field: str, quoted: Quoted) -> Any:
    raw = quoted.value
    if field == "price_rp":
        parsed = parse_rupiah(raw) or _as_int(raw)
        if parsed is None:
            return None
        return as_whole_rupiah(float(parsed))
    if field in {"land_m2", "building_m2"}:
        return _as_float(raw)
    if field in {"bedrooms", "bathrooms"}:
        return _as_int(raw)
    if field == "area":
        return normalize_area(raw, quoted.quote)
    if field == "property_type":
        return _as_property_type(raw, quoted.quote)
    if field == "readiness":
        return _as_readiness(raw, quoted.quote)
    return None


def _reply_text(reply: Any) -> str:
    content = getattr(reply, "content", reply)
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text") or ""))
            else:
                parts.append(getattr(part, "text", str(part)))
        return "".join(parts)
    return "" if content is None else str(content)


def _from_json_blob(text: str) -> TextExtract | None:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return TextExtract.model_validate_json(text[start : end + 1])
    except ValidationError:
        return None


def _call_model(model: Any, description: str) -> TextExtract:
    prompt = _PROMPT.replace("{description}", description)
    bound = getattr(model, "with_structured_output", None)
    if bound is not None:
        try:
            result = bound(TextExtract).invoke(prompt)
            if isinstance(result, TextExtract):
                return result
            return TextExtract.model_validate(result)
        except (ValidationError, ValueError, TypeError):
            pass
    reply = model.invoke(prompt)
    parsed = _from_json_blob(_reply_text(reply))
    return parsed if parsed is not None else TextExtract()


def read_text(record: ListingRecord, model) -> ListingRecord:
    """Fill missing required fields from advert text. Record text evidence for structured fields too."""
    if model is None or not record.description:
        return record
    extracted = _call_model(model, record.description)
    missing = set(record.missing_required())
    for field in REQUIRED_FIELDS:
        quoted = getattr(extracted, field)
        if quoted is None:
            continue
        quote = _quote_in_advert(quoted.quote, record.description)
        if quote is None:
            continue
        if field in missing:
            value = _convert(field, quoted)
            if value is None:
                continue
            setattr(record, field, value)
            record.sources[field] = FieldSource.MODEL
            record.evidence[field] = quote
        else:
            record.evidence.setdefault(field, quote)
    return record
