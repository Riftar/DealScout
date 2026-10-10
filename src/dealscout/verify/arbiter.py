"""Arbiter: sees both values, quotes the Snapshot, settles the field or Quarantines."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from dealscout.domain import (
    Disagreement,
    FieldSource,
    ListingRecord,
    PropertyType,
    Readiness,
    Status,
    normalize_area,
)
from dealscout.verify.checks import run_checks
from dealscout.verify.model import invoke_json

_SPACE = re.compile(r"\s+")

_PROMPT = """You are DealScout's Arbiter. A Scout and a Verifier read different values from the same Snapshot.
Settle the field by quoting the exact words on the page that prove the value.
Return JSON with keys quote and value. Quote must be copied verbatim from the Snapshot.
For price_rp, value is whole Rupiah with no thousand separators.
If the page does not settle it, return JSON with cannot_settle true.

Field: {field}
Scout value: {scout_value}
Verifier value: {verifier_value}

Snapshot:
{html}
"""


class ArbiterCall(BaseModel):
    quote: str | None = None
    value: str | None = None
    cannot_settle: bool = False


def _call_model(model: Any, prompt: str) -> ArbiterCall:
    bound = getattr(model, "with_structured_output", None)
    if bound is not None:
        result = bound(ArbiterCall).invoke(prompt)
        if isinstance(result, ArbiterCall):
            return result
        return ArbiterCall.model_validate(result)
    data = invoke_json(model, prompt)
    if data is None:
        return ArbiterCall(cannot_settle=True)
    return ArbiterCall.model_validate(data)


def _quote_on_page(quote: str | None, html: str) -> bool:
    if not quote or not html:
        return False
    haystack = _SPACE.sub(" ", html.replace("\xa0", " ")).strip().casefold()
    needle = _SPACE.sub(" ", quote.replace("\xa0", " ")).strip().casefold()
    return bool(needle) and needle in haystack


def _as_float(value: str) -> float | None:
    digits = re.sub(r"[^\d]", "", value)
    if len(digits) >= 8:
        try:
            number = float(digits)
        except ValueError:
            return None
        return number if number > 0 else None
    match = re.search(r"(\d+(?:[.,]\d+)?)", value.replace(" ", ""))
    if match is None:
        return None
    raw = match.group(1)
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        number = float(raw)
    except ValueError:
        return None
    return number if number > 0 else None


def _apply(record: ListingRecord, field: str, value: str, quote: str) -> bool:
    converted: Any
    if field == "price_rp":
        amount = _as_float(value)
        converted = int(amount) if amount is not None else None
    elif field in {"land_m2", "building_m2"}:
        converted = _as_float(value)
    elif field in {"bedrooms", "bathrooms"}:
        amount = _as_float(value)
        converted = int(amount) if amount is not None else None
    elif field == "area":
        converted = normalize_area(value) or value.strip()
    elif field == "property_type":
        blob = value.casefold()
        if any(word in blob for word in ("kost", "kosan", "apartemen", "apartment", "ruko", "other")):
            converted = PropertyType.OTHER
        elif any(word in blob for word in ("rumah", "house")):
            converted = PropertyType.HOUSE
        else:
            converted = None
    elif field == "readiness":
        blob = value.casefold()
        if any(word in blob for word in ("indent", "new launch", "primer", "primary")):
            converted = Readiness.INDENT
        elif any(word in blob for word in ("siap huni", "ready", "seken", "sekunder", "secondary")):
            converted = Readiness.READY
        else:
            converted = None
    else:
        converted = value
    if converted is None:
        return False
    setattr(record, field, converted)
    record.sources[field] = FieldSource.ARBITER
    record.evidence[field] = quote
    return True


def arbitrate(
    record: ListingRecord, disagreements: list[Disagreement], html: str, model=None
) -> ListingRecord:
    """Settle each Disagreement from a page quote, or Quarantine. Confirm when clean."""
    for item in disagreements:
        if item.resolved_value is not None:
            continue
        if model is None:
            continue
        prompt = _PROMPT.format(
            field=item.field,
            scout_value=item.scout_value,
            verifier_value=item.verifier_value,
            html=html,
        )
        decision = _call_model(model, prompt)
        if decision.cannot_settle or not _quote_on_page(decision.quote, html) or not decision.value:
            continue
        if not _apply(record, item.field, decision.value, decision.quote):
            continue
        item.resolved_value = decision.value
        item.resolved_by = FieldSource.ARBITER
        item.note = decision.quote

    open_ones = [item for item in disagreements if item.resolved_value is None]
    failures = run_checks(record)
    if failures or open_ones:
        reasons = [failure.detail for failure in failures] + [item.field for item in open_ones]
        record.status = Status.QUARANTINED
        record.status_reason = "; ".join(reasons) or "unresolved disagreement"
        return record
    record.status = Status.CONFIRMED
    record.status_reason = None
    return record
