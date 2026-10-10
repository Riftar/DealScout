"""Call a LangChain chat model for JSON and trim Snapshot HTML for prompts."""

from __future__ import annotations

import re
from typing import Any

from dealscout.verify.util import parse_json_object, reply_text

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def page_text(html: str, limit: int = 12_000) -> str:
    """Plain text from a Snapshot, capped so prompts stay bounded."""
    text = _TAG.sub(" ", html or "")
    text = _SPACE.sub(" ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def invoke_json(model: Any, prompt: str) -> dict[str, Any] | None:
    """One model call; parse the first JSON object from the reply."""
    reply = model.invoke(prompt)
    return parse_json_object(reply_text(reply))
