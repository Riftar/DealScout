"""CLI entry: `dealscout run --area Bintaro --budget 1500000000 --urls data/urls/seed.txt`."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import neatlogs
from dotenv import load_dotenv

from dealscout.domain import Brief, Shortlist
from dealscout.run.graph import run_brief
from dealscout.run.seams import default_seams


def _read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dealscout")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one Brief end to end")
    run.add_argument("--area", required=True)
    run.add_argument("--budget", type=int, required=True, help="Budget in whole Rupiah")
    run.add_argument("--urls", type=Path, required=True, help="Text file of Listing URLs")
    run.add_argument("--headroom", type=float, default=0.05)
    run.add_argument("--snapshot-dir", type=Path, default=Path("data/snapshots"))
    run.add_argument("--out-dir", type=Path, default=None)
    run.add_argument("--state-dir", type=Path, default=Path("data/state"))
    run.add_argument("--land-m2", type=float, default=None)
    run.add_argument("--building-m2", type=float, default=None)
    run.add_argument("--bedrooms", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv(".env")
    args = build_parser().parse_args(argv)
    if args.command != "run":
        return 1

    urls = _read_urls(args.urls)
    if not urls:
        print("no URLs in", args.urls, file=sys.stderr)
        return 1

    brief = Brief(
        area=args.area,
        budget_rp=args.budget,
        headroom=args.headroom,
        land_m2=args.land_m2,
        building_m2=args.building_m2,
        bedrooms=args.bedrooms,
    )
    out_dir = args.out_dir or Path("data/runs") / time.strftime("%Y%m%dT%H%M%SZ")
    seams = default_seams(with_models=True)

    neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="dealscout-run")
    handler = neatlogs.langchain_handler()
    started = time.perf_counter()
    with neatlogs.trace(
        "run",
        kind="WORKFLOW",
        area=brief.area,
        budget_rp=brief.budget_rp,
        url_count=len(urls),
    ) as root:
        final = run_brief(
            brief,
            urls,
            snapshot_dir=args.snapshot_dir,
            out_dir=out_dir,
            state_dir=args.state_dir,
            seams=seams,
            callbacks=[handler],
        )
        span_ctx = root.get_span_context()
        trace_id = format(span_ctx.trace_id, "032x")
    wall = time.perf_counter() - started
    flushed = neatlogs.flush()
    neatlogs.shutdown()

    shortlist = Shortlist.model_validate(final["shortlist"])
    print(f"area={shortlist.brief.area} budget={shortlist.brief.budget_rp}")
    print(
        f"confirmed={shortlist.confirmed} quarantined={shortlist.quarantined} "
        f"unreachable={shortlist.unreachable} deals={len(shortlist.deals)}"
    )
    for deal in shortlist.deals:
        print(
            f"  #{deal.rank} ratio={deal.valuation.ratio:.3f} "
            f"ask={deal.record.price_rp} expected={deal.valuation.expected_price_rp} "
            f"{deal.record.url}"
        )
    print(f"report={final.get('report_path')}")
    print(f"trace_id={trace_id}")
    plan = final.get("plan") or {}
    if plan.get("total_tokens") is not None:
        print(f"tokens={plan['total_tokens']} (prompt={plan.get('prompt_tokens')} completion={plan.get('completion_tokens')})")
    print(f"wall_seconds={wall:.1f} neatlogs_flush={'ok' if flushed else 'FAILED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
