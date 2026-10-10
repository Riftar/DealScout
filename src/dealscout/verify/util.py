"""Shared helpers for reading a model reply and quoting a Snapshot."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_SPACE = re.compile(r"\s+")


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


def quote_on_page(quote: str, html: str) -> bool:
    """True when quote appears in the Snapshot HTML, ignoring extra whitespace."""
    if not quote or not quote.strip() or not html:
        return False
    if quote in html:
        return True
    collapsed_quote = _SPACE.sub(" ", quote).strip().lower()
    collapsed_html = _SPACE.sub(" ", html).lower()
    return bool(collapsed_quote) and collapsed_quote in collapsed_html
