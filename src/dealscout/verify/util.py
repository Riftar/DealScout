"""Shared helpers for reading a model reply and quoting a Snapshot."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_SPACE = re.compile(r"\s+")

# Asking prices on Indonesian portals are often juta/miliar, not whole Rupiah.
MIN_PRICE_RP = 100_000_000
MAX_PRICE_RP = 100_000_000_000
PRICE_MATCH_LIMIT = 0.15
_PRICE_SCALES = (1, 1_000, 1_000_000, 1_000_000_000)


def reply_text(reply: Any) -> str:
    """Pull the text out of a LangChain-style reply or a plain string."""
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


def parse_json_object(text: str) -> dict[str, Any] | None:
    """Read the first JSON object from a model reply. None when it is not JSON."""
    blob = _FENCE.sub("", text.strip()).strip()
    start = blob.find("{")
    end = blob.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(blob[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _in_price_range(amount: float) -> bool:
    return MIN_PRICE_RP <= amount <= MAX_PRICE_RP


def as_whole_rupiah(amount: float, peer: float | None = None) -> int | None:
    """Turn a juta/miliar-scale figure into whole Rupiah.

    When `peer` is a whole-Rupiah price, pick the scale that lands closest to it
    inside the allowed range. Without a peer, 100–9999 is juta and 10_000–99_999_999
    is ribu (so 885 → 885_000_000 and 850_000 → 850_000_000).
    """
    if amount <= 0:
        return None
    if peer is not None and peer > 0:
        scored: list[tuple[float, float]] = []
        for scale in _PRICE_SCALES:
            scaled = amount * scale
            if _in_price_range(scaled):
                scored.append((abs(scaled - peer) / max(peer, 1.0), scaled))
        if scored:
            scored.sort(key=lambda item: item[0])
            return int(round(scored[0][1]))
    if _in_price_range(amount):
        return int(round(amount))
    if 100 <= amount < 10_000:
        return int(round(amount * 1_000_000))
    if 10_000 <= amount < MIN_PRICE_RP:
        scaled = amount * 1_000
        if _in_price_range(scaled):
            return int(round(scaled))
    return int(round(amount))


def prices_agree(left: float, right: float, *, limit: float = PRICE_MATCH_LIMIT) -> bool:
    """True when two price readings are the same amount of Rupiah.

    Two whole-Rupiah figures must match exactly. If exactly one side looks like
    juta or ribu, it is scaled toward the other and compared within `limit`.
    Two small figures share one scale and must then match exactly (60 vs 62
    is not a price match).
    """
    if left <= 0 or right <= 0:
        return False
    left_in = _in_price_range(left)
    right_in = _in_price_range(right)
    if left_in and right_in:
        return int(round(left)) == int(round(right))
    if left_in != right_in:
        peer = left if left_in else right
        other = right if left_in else left
        scaled = as_whole_rupiah(other, peer)
        if scaled is None:
            return False
        return abs(scaled - peer) / peer <= limit
    for scale in (1_000_000, 1_000, 1_000_000_000):
        a = left * scale
        b = right * scale
        if _in_price_range(a) and _in_price_range(b):
            return int(round(a)) == int(round(b))
    return False


def quote_on_page(quote: str, html: str) -> bool:
    """True when quote appears in the Snapshot HTML, ignoring extra whitespace."""
    if not quote or not quote.strip() or not html:
        return False
    if quote in html:
        return True
    collapsed_quote = _SPACE.sub(" ", quote).strip().lower()
    collapsed_html = _SPACE.sub(" ", html).lower()
    return bool(collapsed_quote) and collapsed_quote in collapsed_html
