"""Chat models for the Scout (fast) and the Verifier (strong)."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def _chat(model_name: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        temperature=0,
        timeout=120,
    )


def scout_model() -> ChatOpenAI:
    """The Scout's model: plan, text read, recover re-read."""
    return _chat(os.environ["LLM_MODEL_FAST"])


def verifier_model() -> ChatOpenAI:
    """The Verifier's model: a different one from the Scout's."""
    return _chat(os.environ["LLM_MODEL_STRONG"])
