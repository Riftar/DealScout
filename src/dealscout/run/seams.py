"""Resolve each lane seam: real module when present, otherwise the integration fake."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dealscout.collect.fetcher import Fetcher
from dealscout.domain import Brief, ListingRecord, MarketPrice, Shortlist, Snapshot, Valuation
from dealscout.extract.structured import read_structured
from dealscout.run import fakes


def _optional(module: str, name: str, fallback: Callable) -> Callable:
    try:
        imported = __import__(module, fromlist=[name])
        return getattr(imported, name)
    except (ImportError, AttributeError):
        return fallback


@dataclass
class Seams:
    fetcher_factory: Callable[[Path], Fetcher]
    read_structured: Callable[[str, str, str], ListingRecord]
    read_text: Callable[..., ListingRecord]
    run_checks: Callable[[ListingRecord], list]
    verify: Callable[..., list]
    arbitrate: Callable[..., ListingRecord]
    market_price: Callable[[str, list[ListingRecord]], MarketPrice | None]
    value: Callable[[ListingRecord, MarketPrice], Valuation]
    shortlist: Callable[[Brief, list[ListingRecord]], Shortlist]
    write_report: Callable[[Shortlist, Path], Path]
    scout_model: Any = None
    verifier_model: Any = None


def default_seams(*, with_models: bool = False) -> Seams:
    scout = verifier = None
    if with_models:
        from dealscout.run.llm import scout_model, verifier_model

        scout = scout_model()
        verifier = verifier_model()
    return Seams(
        fetcher_factory=lambda snapshot_dir: Fetcher(snapshot_dir),
        read_structured=read_structured,
        read_text=_optional("dealscout.extract.text", "read_text", fakes.read_text),
        run_checks=_optional("dealscout.verify.checks", "run_checks", fakes.run_checks),
        verify=_optional("dealscout.verify.verifier", "verify", fakes.verify),
        arbitrate=_optional("dealscout.verify.arbiter", "arbitrate", fakes.arbitrate),
        market_price=_optional("dealscout.value.market", "market_price", fakes.market_price),
        value=_optional("dealscout.value.valuation", "value", fakes.value),
        shortlist=_optional("dealscout.value.valuation", "shortlist", fakes.shortlist),
        write_report=_optional("dealscout.report.html", "write_report", fakes.write_report),
        scout_model=scout,
        verifier_model=verifier,
    )


def load_html(snapshot: Snapshot) -> str:
    if not snapshot.path:
        return ""
    return Path(snapshot.path).read_text(encoding="utf-8", errors="replace")
