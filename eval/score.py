"""Score a Run's JSON against eval/answer_key.jsonl.

Prints field accuracy, true Deals in the top 10, cost per Run, time per Run,
and appends one row to evidence/scores.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
DEFAULT_KEY = EVAL_DIR / "answer_key.jsonl"
DEFAULT_CSV = ROOT / "evidence" / "scores.csv"

REQUIRED_FIELDS = (
    "price_rp",
    "land_m2",
    "building_m2",
    "bedrooms",
    "bathrooms",
    "area",
    "property_type",
    "readiness",
)

CSV_COLUMNS = (
    "run_id",
    "field_accuracy",
    "true_deals_in_top_10",
    "cost_per_run",
    "time_per_run",
    "scored_at",
)


def load_answer_key(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        url = row.get("url")
        if not url:
            continue
        rows[url] = row
    return rows


def _records(run: dict[str, Any]) -> list[dict[str, Any]]:
    if run.get("records"):
        return list(run["records"])
    records: list[dict[str, Any]] = []
    shortlist = run.get("shortlist") or run
    for deal in shortlist.get("deals") or []:
        record = deal.get("record")
        if record:
            records.append(record)
    for extra in ("quarantined_listings", "unreachable_listings", "quarantined", "unreachable"):
        rows = run.get(extra)
        if isinstance(rows, list) and rows and isinstance(rows[0], dict) and "url" in rows[0]:
            records.extend(rows)
    return records


def _top_deals(run: dict[str, Any], n: int = 10) -> list[dict[str, Any]]:
    shortlist = run.get("shortlist") or run
    deals = list(shortlist.get("deals") or [])
    deals.sort(key=lambda deal: deal.get("rank") if deal.get("rank") is not None else 10**9)
    return deals[:n]


def _norm(field: str, value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "value"):
        value = value.value
    if field in {"price_rp", "bedrooms", "bathrooms"}:
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return str(value).strip()
    if field in {"land_m2", "building_m2"}:
        try:
            return round(float(value), 1)
        except (TypeError, ValueError):
            return str(value).strip()
    return str(value).strip().lower()


def field_matches(expected: Any, observed: Any, field: str) -> bool:
    left = _norm(field, expected)
    right = _norm(field, observed)
    if left is None or right is None:
        return left is None and right is None
    return left == right


def record_matches_key(record: dict[str, Any], key_row: dict[str, Any]) -> bool:
    return all(field_matches(key_row.get(field), record.get(field), field) for field in REQUIRED_FIELDS)


def score_run(run: dict[str, Any], key: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_url = {row["url"]: row for row in _records(run) if row.get("url")}
    scored = 0
    correct = 0
    for url, key_row in key.items():
        record = by_url.get(url)
        if record is None:
            continue
        for field in REQUIRED_FIELDS:
            scored += 1
            if field_matches(key_row.get(field), record.get(field), field):
                correct += 1
    accuracy = (correct / scored) if scored else 0.0

    true_deals = 0
    for deal in _top_deals(run, 10):
        record = deal.get("record") or {}
        url = record.get("url") or deal.get("url")
        key_row = key.get(url) if url else None
        if key_row is None:
            continue
        if record_matches_key(record, key_row):
            true_deals += 1

    cost = run.get("cost_usd")
    if cost is None:
        cost = run.get("cost_per_run")
    time_s = run.get("duration_s")
    if time_s is None:
        time_s = run.get("time_per_run")
    if time_s is None:
        time_s = run.get("wall_seconds")

    return {
        "run_id": run.get("run_id") or run.get("thread_id") or "",
        "field_accuracy": round(float(accuracy), 6),
        "true_deals_in_top_10": int(true_deals),
        "cost_per_run": None if cost is None else round(float(cost), 6),
        "time_per_run": None if time_s is None else round(float(time_s), 4),
        "fields_scored": scored,
        "fields_correct": correct,
    }


def append_scores_csv(row: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.is_file()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "run_id": row.get("run_id") or "",
                "field_accuracy": row["field_accuracy"],
                "true_deals_in_top_10": row["true_deals_in_top_10"],
                "cost_per_run": row["cost_per_run"],
                "time_per_run": row["time_per_run"],
                "scored_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )


def _print(row: dict[str, Any]) -> None:
    cost = row["cost_per_run"]
    time_s = row["time_per_run"]
    print(f"field_accuracy={row['field_accuracy']}")
    print(f"true_deals_in_top_10={row['true_deals_in_top_10']}")
    print(f"cost_per_run={cost if cost is not None else ''}")
    print(f"time_per_run={time_s if time_s is not None else ''}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score a DealScout Run JSON against the answer key.")
    parser.add_argument("run_json", type=Path, help="Path to a Run JSON file")
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY, help="answer_key.jsonl")
    parser.add_argument("--out", type=Path, default=DEFAULT_CSV, help="scores.csv to append")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.run_json.is_file():
        print(f"missing Run JSON: {args.run_json}", file=sys.stderr)
        return 1
    if not args.key.is_file():
        print(f"missing answer key: {args.key}", file=sys.stderr)
        return 1
    run = json.loads(args.run_json.read_text(encoding="utf-8"))
    key = load_answer_key(args.key)
    if not args.run_json.stem == "ignore" and "run_id" not in run:
        run["run_id"] = args.run_json.stem
    row = score_run(run, key)
    if not row.get("run_id"):
        row["run_id"] = args.run_json.stem
    append_scores_csv(row, args.out)
    _print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
