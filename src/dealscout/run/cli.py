"""CLI entry.

`dealscout run --area Bintaro --budget 1500000000 --urls data/urls/seed.txt` runs one Brief.
`dealscout dashboard` serves the Dashboard; `dealscout tick` fires the Jobs that are due.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import neatlogs
from dotenv import load_dotenv

from dealscout.dashboard.schedule import read_urls
from dealscout.domain import Brief, Shortlist
from dealscout.run.graph import run_brief
from dealscout.run.seams import default_seams

JOBS_DB = "jobs.sqlite"


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

    dashboard = sub.add_parser("dashboard", help="Serve the Dashboard")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8000)
    dashboard.add_argument("--state-dir", type=Path, default=Path("data/state"))

    tick = sub.add_parser("tick", help="Queue the Jobs due now and carry out one queued Run")
    tick.add_argument("--state-dir", type=Path, default=Path("data/state"))
    tick.add_argument("--snapshot-dir", type=Path, default=Path("data/snapshots"))
    tick.add_argument("--urls-dir", type=Path, default=Path("data/urls"))
    return parser


def execute_run(
    brief: Brief,
    urls: list[str],
    *,
    snapshot_dir: Path,
    out_dir: Path,
    state_dir: Path,
    thread_id: str | None = None,
) -> tuple[dict, str, float]:
    """One traced Run with live models. Returns the final state, trace id and wall seconds."""
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
            snapshot_dir=snapshot_dir,
            out_dir=out_dir,
            state_dir=state_dir,
            seams=seams,
            thread_id=thread_id,
            callbacks=[handler],
        )
        span_ctx = root.get_span_context()
        trace_id = format(span_ctx.trace_id, "032x")
    wall = time.perf_counter() - started
    final["neatlogs_flushed"] = bool(neatlogs.flush())
    neatlogs.shutdown()
    return final, trace_id, wall


def _dashboard(args: argparse.Namespace) -> int:
    from dealscout.dashboard.app import Dashboard, serve, spawn_tick
    from dealscout.dashboard.store import JobStore

    store = JobStore(args.state_dir / JOBS_DB)
    print(f"Dashboard on http://{args.host}:{args.port}", flush=True)
    serve(Dashboard(store, kick=spawn_tick(args.state_dir)), args.host, args.port)
    return 0


def _tick(args: argparse.Namespace) -> int:
    from dealscout.dashboard.app import spawn_tick
    from dealscout.dashboard.schedule import tick
    from dealscout.dashboard.store import JobStore

    def execute(brief: Brief, urls: list[str], out_dir: Path, thread_id: str) -> tuple[dict, str]:
        final, trace_id, _ = execute_run(
            brief,
            urls,
            snapshot_dir=args.snapshot_dir,
            out_dir=out_dir,
            state_dir=args.state_dir,
            thread_id=thread_id,
        )
        return final, trace_id

    seams = default_seams()
    run = tick(
        JobStore(args.state_dir / JOBS_DB),
        execute=execute,
        market_price=seams.market_price,
        value=seams.value,
        urls_dir=args.urls_dir,
        kick=spawn_tick(args.state_dir),
    )
    if run is not None:
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        print(f"{stamp} job={run.job_id} run={run.id} state={run.state.value} trace_id={run.trace_id}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    load_dotenv(".env")
    args = build_parser().parse_args(argv)
    if args.command == "dashboard":
        return _dashboard(args)
    if args.command == "tick":
        return _tick(args)

    urls = read_urls(args.urls)
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
    final, trace_id, wall = execute_run(
        brief,
        urls,
        snapshot_dir=args.snapshot_dir,
        out_dir=out_dir,
        state_dir=args.state_dir,
    )
    flushed = final["neatlogs_flushed"]

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
