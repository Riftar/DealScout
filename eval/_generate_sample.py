"""One-shot builder for answer_key.jsonl and sample_run.json. Not imported at score time."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREAS = [
    ("Bintaro", "bintaro"),
    ("BSD/Serpong", "bsd"),
    ("Gading Serpong", "gading"),
    ("Depok", "depok"),
    ("Yogyakarta", "yogya"),
    ("Sleman", "sleman"),
    ("Bantul", "bantul"),
]


def rows() -> list[dict]:
    out: list[dict] = [
        {
            "url": "https://www.rumah123.com/en/property/tangerang-selatan-bintaro/fixture-hos1/",
            "price_rp": 875_000_000,
            "land_m2": 55.0,
            "building_m2": 60.0,
            "bedrooms": 2,
            "bathrooms": 2,
            "area": "Bintaro",
            "property_type": "house",
            "readiness": "ready",
        },
        {
            "url": "https://www.99.co/id/properti/fixture-bsd",
            "price_rp": 1_100_000_000,
            "land_m2": 57.0,
            "building_m2": 60.0,
            "bedrooms": 2,
            "bathrooms": 2,
            "area": "BSD/Serpong",
            "property_type": "house",
            "readiness": "ready",
        },
    ]
    # 38 documented-sample rows: cycle the seven Areas.
    n = 0
    while len(out) < 40:
        area, slug = AREAS[n % len(AREAS)]
        seq = n + 1
        land = float(70 + (n * 3) % 40)
        building = float(50 + (n * 2) % 35)
        beds = 2 + (n % 3)
        baths = 1 + (n % 3)
        price = 750_000_000 + n * 15_000_000
        indent = n % 13 == 0
        out.append(
            {
                "url": f"https://example.test/listings/{slug}-{seq:02d}",
                "price_rp": price,
                "land_m2": land,
                "building_m2": building,
                "bedrooms": beds,
                "bathrooms": baths,
                "area": area,
                "property_type": "house",
                "readiness": "indent" if indent else "ready",
            }
        )
        n += 1
    # Eight gold Deals for the ranked Shortlist: the rumah123 fixture plus seven
    # Ready documented-sample rows. Indent rows stay out. The flag is not written
    # to the answer key (URL and field values only).
    marked = 0
    for row in out:
        if row["readiness"] != "ready":
            continue
        if "99.co" in row["url"]:
            continue
        row["_gold"] = True
        if "example.test" in row["url"]:
            row["price_rp"] = int(row["price_rp"] * 0.72)
        marked += 1
        if marked == 8:
            break
    return out


def as_record(row: dict) -> dict:
    return {
        "url": row["url"],
        "portal": "example" if "example.test" in row["url"] else ("rumah123" if "rumah123" in row["url"] else "99co"),
        "listing_id": None,
        "price_rp": row["price_rp"],
        "land_m2": row["land_m2"],
        "building_m2": row["building_m2"],
        "bedrooms": row["bedrooms"],
        "bathrooms": row["bathrooms"],
        "area": row["area"],
        "property_type": row["property_type"],
        "readiness": row["readiness"],
        "title": None,
        "description": None,
        "detail_location": None,
        "certificate": None,
        "floors": None,
        "furnishing": None,
        "electricity_w": None,
        "year_built": None,
        "sources": {},
        "evidence": {},
        "status": "confirmed",
        "status_reason": None,
        "duplicate_of": None,
    }


def market() -> dict:
    return {
        "area": "Bintaro",
        "comp_count": 3,
        "median_rp_per_land_m2": 10_000_000,
        "median_rp_per_building_m2": 12_000_000,
        "comp_urls": [
            "https://example.test/comp/a",
            "https://example.test/comp/b",
            "https://example.test/comp/c",
        ],
    }


def as_deal(row: dict, rank: int) -> dict:
    expected = 1_000_000_000
    ask = row["price_rp"]
    ratio = ask / expected
    return {
        "record": as_record(row),
        "valuation": {
            "url": row["url"],
            "expected_price_rp": expected,
            "ratio": ratio,
            "tier": "below_market",
            "land_ratio": ratio,
            "building_ratio": ratio,
            "split": False,
            "market": market(),
        },
        "rank": rank,
        "soft_misses": [],
    }


def main() -> None:
    key = rows()
    key_path = ROOT / "eval" / "answer_key.jsonl"
    published = [{k: v for k, v in row.items() if not k.startswith("_")} for row in key]
    key_path.write_text("".join(json.dumps(row) + "\n" for row in published), encoding="utf-8")

    records = [as_record(row) for row in key]
    # Four single-field errors so field accuracy is 316/320 = 0.9875.
    records[1]["bedrooms"] = 3  # 99.co fixture gold is 2
    records[5]["price_rp"] = records[5]["price_rp"] + 50_000_000
    records[10]["land_m2"] = None
    records[20]["area"] = "Depok" if records[20]["area"] != "Depok" else "Bintaro"

    true_rows = [row for row in key if row.get("_gold")]
    decoy_rows = [row for row in key if not row.get("_gold")]
    ranked = true_rows[:7] + decoy_rows[:5]
    deals = [as_deal(row, i) for i, row in enumerate(ranked, start=1)]

    run = {
        "brief": {"area": "Bintaro", "budget_rp": 1_500_000_000, "headroom": 0.05},
        "records": records,
        "shortlist": {
            "brief": {
                "area": "Bintaro",
                "budget_rp": 1_500_000_000,
                "headroom": 0.05,
                "land_m2": None,
                "building_m2": None,
                "bedrooms": None,
                "soft_tolerance": 0.2,
            },
            "deals": deals,
            "considered": 40,
            "confirmed": 40,
            "quarantined": 0,
            "unreachable": 0,
        },
        "cost_usd": 0.012,
        "wall_seconds": 39.3,
        "note": (
            "Sample Run JSON for eval/score.py. Field values are from the handwritten "
            "fixtures plus the documented sample, not a live Portal fetch. "
            "cost_usd and wall_seconds are placeholders (wall_seconds matches the "
            "first traced Run on main: 39.3 s)."
        ),
    }
    run_path = ROOT / "eval" / "sample_run.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(f"wrote {key_path} ({len(published)} rows, gold={sum(1 for r in key if r.get('_gold'))})")
    print(f"wrote {run_path} (deals={len(deals)})")


if __name__ == "__main__":
    main()
