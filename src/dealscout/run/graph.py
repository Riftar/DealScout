"""One Run as a LangGraph graph with a SQLite checkpointer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from dealscout.collect.duplicates import mark_duplicates
from dealscout.collect.fetcher import portal_of
from dealscout.domain import Brief, ListingRecord, Shortlist, Snapshot, Status
from dealscout.run.seams import Seams, default_seams, load_html


class RunState(TypedDict, total=False):
    brief: dict
    urls: list[str]
    plan: dict
    snapshots: list[dict]
    records: list[dict]
    confirmed: list[dict]
    quarantined: list[dict]
    unreachable: list[dict]
    shortlist: dict
    report_path: str
    fetch_retries: dict[str, int]
    check_retries: dict[str, int]
    snapshot_dir: str
    out_dir: str


def _dump_records(records: list[ListingRecord]) -> list[dict]:
    return [r.model_dump(mode="json") for r in records]


def _load_records(rows: list[dict]) -> list[ListingRecord]:
    return [ListingRecord.model_validate(row) for row in rows]


def _dump_snapshots(rows: list[Snapshot]) -> list[dict]:
    return [s.model_dump(mode="json") for s in rows]


def _load_snapshots(rows: list[dict]) -> list[Snapshot]:
    return [Snapshot.model_validate(row) for row in rows]


def build_graph(seams: Seams, checkpointer: SqliteSaver | None = None):
    """Compile the Run graph. Nodes call lane seams (or fakes)."""

    def plan(state: RunState) -> dict:
        brief = Brief.model_validate(state["brief"])
        urls = state["urls"]
        plan_body = {
            "area": brief.area,
            "budget_rp": brief.budget_rp,
            "headroom": brief.headroom,
            "sources": sorted({portal_of(url) for url in urls}),
            "page_budget": len(urls),
            "comp_window": "same_area",
            "urls": urls,
        }
        if seams.scout_model is not None:
            reply = seams.scout_model.invoke(
                "You are planning a DealScout Run. Reply with one short sentence confirming "
                f"you will cover area {brief.area} with {len(urls)} listing URLs "
                f"from portals {', '.join(plan_body['sources'])}."
            )
            usage = getattr(reply, "usage_metadata", None) or {}
            plan_body["prompt_tokens"] = usage.get("input_tokens")
            plan_body["completion_tokens"] = usage.get("output_tokens")
            plan_body["total_tokens"] = usage.get("total_tokens")
        return {"plan": plan_body}

    def collect(state: RunState) -> dict:
        fetcher = seams.fetcher_factory(Path(state["snapshot_dir"]))
        snapshots = _load_snapshots(state.get("snapshots") or [])
        by_url = {s.url: s for s in snapshots}
        for url in state["urls"]:
            if url in by_url and by_url[url].reachable:
                continue
            by_url[url] = fetcher.fetch(url)
        return {"snapshots": _dump_snapshots(list(by_url.values()))}

    def extract(state: RunState) -> dict:
        snapshots = _load_snapshots(state.get("snapshots") or [])
        existing = {r.url: r for r in _load_records(state.get("records") or [])}
        records: list[ListingRecord] = []
        for snap in snapshots:
            if not snap.reachable:
                continue
            if snap.url in existing and existing[snap.url].status is Status.CONFIRMED:
                records.append(existing[snap.url])
                continue
            html = load_html(snap)
            record = seams.read_structured(html, snap.url, snap.portal)
            try:
                record = seams.read_text(record, seams.scout_model)
            except Exception:
                # A bad model reply must not kill the Run; checks will Quarantine if needed.
                pass
            records.append(record)
        mark_duplicates(records)
        return {"records": _dump_records(records)}

    def check(state: RunState) -> dict:
        snapshots = {s.url: s for s in _load_snapshots(state.get("snapshots") or [])}
        records = _load_records(state.get("records") or [])
        confirmed: list[ListingRecord] = []
        quarantined: list[ListingRecord] = []
        pending: list[ListingRecord] = []
        for record in records:
            if record.status is Status.CONFIRMED:
                confirmed.append(record)
                continue
            if record.status is Status.QUARANTINED:
                quarantined.append(record)
                continue
            snap = snapshots.get(record.url)
            html = load_html(snap) if snap else ""
            failures = seams.run_checks(record)
            try:
                disagreements = seams.verify(record, html, seams.verifier_model)
            except Exception:
                disagreements = []
            if failures or disagreements:
                # Leave unsettled for Recover; stash the failure note.
                record.status_reason = "; ".join(
                    [f.detail for f in failures] + [d.field for d in disagreements]
                )
                pending.append(record)
                continue
            settled = seams.arbitrate(record, disagreements, html, seams.verifier_model)
            if settled.status is Status.CONFIRMED:
                confirmed.append(settled)
            else:
                quarantined.append(settled)
        # Pending stay in records for Recover; also keep confirmed/quarantined lists.
        all_records = confirmed + quarantined + pending
        return {
            "records": _dump_records(all_records),
            "confirmed": _dump_records(confirmed),
            "quarantined": _dump_records(quarantined),
        }

    def recover(state: RunState) -> dict:
        fetcher = seams.fetcher_factory(Path(state["snapshot_dir"]))
        snapshots = {s.url: s for s in _load_snapshots(state.get("snapshots") or [])}
        fetch_retries = dict(state.get("fetch_retries") or {})
        check_retries = dict(state.get("check_retries") or {})
        confirmed = _load_records(state.get("confirmed") or [])
        quarantined = _load_records(state.get("quarantined") or [])
        unreachable: list[ListingRecord] = _load_records(state.get("unreachable") or [])
        records = _load_records(state.get("records") or [])
        pending = [
            r
            for r in records
            if r.status is None and r.url not in {c.url for c in confirmed + quarantined + unreachable}
        ]

        # Failed fetches: one retry, then Unreachable.
        for url in state["urls"]:
            snap = snapshots.get(url)
            if snap is not None and snap.reachable:
                continue
            if fetch_retries.get(url, 0) >= 1:
                if not any(u.url == url for u in unreachable):
                    unreachable.append(
                        ListingRecord(
                            url=url,
                            portal=portal_of(url),
                            status=Status.UNREACHABLE,
                            status_reason=(snap.unreachable_reason if snap else "unreachable"),
                        )
                    )
                continue
            fetch_retries[url] = fetch_retries.get(url, 0) + 1
            snap = fetcher.fetch(url)
            snapshots[url] = snap
            if not snap.reachable:
                unreachable.append(
                    ListingRecord(
                        url=url,
                        portal=snap.portal,
                        status=Status.UNREACHABLE,
                        status_reason=snap.unreachable_reason or "unreachable",
                    )
                )
                continue
            html = load_html(snap)
            record = seams.read_structured(html, snap.url, snap.portal)
            try:
                record = seams.read_text(record, seams.scout_model)
            except Exception:
                pass
            pending.append(record)

        # Failed checks: one re-extract, then Quarantine.
        still_pending: list[ListingRecord] = []
        for record in pending:
            html = load_html(snapshots[record.url]) if record.url in snapshots else ""
            failures = seams.run_checks(record)
            try:
                disagreements = seams.verify(record, html, seams.verifier_model)
            except Exception:
                disagreements = []
            if not failures and not disagreements:
                try:
                    settled = seams.arbitrate(record, disagreements, html, seams.verifier_model)
                except Exception:
                    settled = record
                    settled.status = Status.QUARANTINED
                    settled.status_reason = settled.status_reason or "arbiter failed"
                if settled.status is Status.CONFIRMED:
                    confirmed.append(settled)
                else:
                    quarantined.append(settled)
                continue
            if check_retries.get(record.url, 0) >= 1:
                record.status = Status.QUARANTINED
                record.status_reason = record.status_reason or "; ".join(f.detail for f in failures)
                quarantined.append(record)
                continue
            check_retries[record.url] = check_retries.get(record.url, 0) + 1
            feedback = record.status_reason or "; ".join(f.detail for f in failures)
            record.status_reason = f"retry after: {feedback}"
            try:
                record = seams.read_text(record, seams.scout_model)
            except Exception:
                pass
            failures = seams.run_checks(record)
            try:
                disagreements = seams.verify(record, html, seams.verifier_model)
            except Exception:
                disagreements = []
            try:
                settled = seams.arbitrate(record, disagreements, html, seams.verifier_model)
            except Exception:
                settled = record
                settled.status = Status.QUARANTINED
                settled.status_reason = settled.status_reason or feedback
            if settled.status is Status.CONFIRMED and not failures:
                confirmed.append(settled)
            else:
                if settled.status is not Status.QUARANTINED:
                    settled.status = Status.QUARANTINED
                    settled.status_reason = settled.status_reason or feedback
                quarantined.append(settled)

        all_records = confirmed + quarantined + unreachable + still_pending
        mark_duplicates(all_records)
        return {
            "snapshots": _dump_snapshots(list(snapshots.values())),
            "records": _dump_records(all_records),
            "confirmed": _dump_records(confirmed),
            "quarantined": _dump_records(quarantined),
            "unreachable": _dump_records(unreachable),
            "fetch_retries": fetch_retries,
            "check_retries": check_retries,
        }

    def value_step(state: RunState) -> dict:
        # Valuation is folded into shortlist for the fake; keep a node for the audit trail.
        return {}

    def rank(state: RunState) -> dict:
        brief = Brief.model_validate(state["brief"])
        confirmed = _load_records(state.get("confirmed") or [])
        quarantined = _load_records(state.get("quarantined") or [])
        unreachable = _load_records(state.get("unreachable") or [])
        unique = [record for record in confirmed if not record.duplicate_of]
        result = seams.shortlist(brief, unique)
        result.quarantined = len(quarantined)
        result.unreachable = len(unreachable)
        result.considered = len(confirmed) + len(quarantined) + len(unreachable)
        result.confirmed = len(confirmed)
        result.quarantined_listings = quarantined
        result.unreachable_listings = unreachable
        return {"shortlist": result.model_dump(mode="json")}

    def report(state: RunState) -> dict:
        shortlist = Shortlist.model_validate(state["shortlist"])
        path = seams.write_report(shortlist, Path(state["out_dir"]))
        return {"report_path": path.as_posix()}

    graph = StateGraph(RunState)
    graph.add_node("plan", plan)
    graph.add_node("collect", collect)
    graph.add_node("extract", extract)
    graph.add_node("check", check)
    graph.add_node("recover", recover)
    graph.add_node("value", value_step)
    graph.add_node("rank", rank)
    graph.add_node("report", report)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "collect")
    graph.add_edge("collect", "extract")
    graph.add_edge("extract", "check")
    graph.add_edge("check", "recover")
    graph.add_edge("recover", "value")
    graph.add_edge("value", "rank")
    graph.add_edge("rank", "report")
    graph.add_edge("report", END)
    return graph.compile(checkpointer=checkpointer)


def run_brief(
    brief: Brief,
    urls: list[str],
    *,
    snapshot_dir: Path,
    out_dir: Path,
    state_dir: Path,
    seams: Seams | None = None,
    thread_id: str | None = None,
    callbacks: list | None = None,
) -> dict:
    """Execute one Run, checkpointed under state_dir, and return the final state."""
    seams = seams or default_seams()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    thread_id = thread_id or f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    db_path = state_dir / "runs.sqlite"
    initial: RunState = {
        "brief": brief.model_dump(mode="json"),
        "urls": urls,
        "snapshots": [],
        "records": [],
        "confirmed": [],
        "quarantined": [],
        "unreachable": [],
        "fetch_retries": {},
        "check_retries": {},
        "snapshot_dir": snapshot_dir.as_posix(),
        "out_dir": out_dir.as_posix(),
    }
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    if callbacks:
        config["callbacks"] = callbacks
    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        checkpointer.setup()
        app = build_graph(seams, checkpointer)
        return app.invoke(initial, config=config)
