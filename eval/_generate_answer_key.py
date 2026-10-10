"""One-shot builder for eval/answer_key.jsonl. Not part of the Run."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def row(
    url: str,
    *,
    price_rp: int | None,
    land_m2: float | None,
    building_m2: float | None,
    bedrooms: int | None,
    bathrooms: int | None,
    area: str | None,
    property_type: str | None,
    readiness: str | None,
) -> dict:
    return {
        "url": url,
        "price_rp": price_rp,
        "land_m2": land_m2,
        "building_m2": building_m2,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "area": area,
        "property_type": property_type,
        "readiness": readiness,
    }


def main() -> None:
    # Two rows read from the hand-written extract fixtures (no real advert HTML).
    fixtures = [
        row(
            "https://www.rumah123.com/en/property/x-hos1/",
            price_rp=875_000_000,
            land_m2=55,
            building_m2=60,
            bedrooms=2,
            bathrooms=2,
            area="Bintaro",
            property_type="house",
            readiness=None,
        ),
        row(
            "https://www.99.co/id/properti/x",
            price_rp=1_100_000_000,
            land_m2=57,
            building_m2=60,
            bedrooms=2,
            bathrooms=2,
            area="BSD/Serpong",
            property_type="house",
            readiness="ready",
        ),
    ]
    # Hand-made rows. Prices sit around 8-12 million Rp / m2 so Bintaro yields Deals.
    handmade = [
        ("001", "Bintaro", 100, 80, 3, 2, 700_000_000, "house", "ready"),
        ("002", "Bintaro", 110, 85, 3, 2, 1_200_000_000, "house", "ready"),
        ("003", "Bintaro", 90, 70, 3, 2, 950_000_000, "house", "ready"),
        ("004", "Bintaro", 80, 60, 2, 2, 650_000_000, "house", "ready"),
        ("005", "Bintaro", 120, 90, 4, 3, 1_450_000_000, "house", "ready"),
        ("006", "Bintaro", 80, 60, 2, 2, 980_000_000, "house", "ready"),
        ("007", "Bintaro", 100, 80, 3, 2, 980_000_000, "house", "ready"),
        ("008", "Bintaro", 105, 82, 3, 2, 1_050_000_000, "house", "ready"),
        ("009", "Bintaro", 70, 55, 2, 1, 890_000_000, "house", "ready"),
        ("010", "Bintaro", 150, 120, 4, 3, 2_000_000_000, "house", "ready"),
        ("011", "Bintaro", 100, 80, 3, 2, 750_000_000, "house", "indent"),
        ("012", "Bintaro", 90, 80, 8, 8, 400_000_000, "other", "ready"),
        ("013", "BSD/Serpong", 72, 90, 3, 2, 960_000_000, "house", "ready"),
        ("014", "BSD/Serpong", 60, 70, 2, 2, 850_000_000, "house", "ready"),
        ("015", "BSD/Serpong", 84, 90, 3, 2, 1_100_000_000, "house", "ready"),
        ("016", "BSD/Serpong", 55, 60, 2, 1, 780_000_000, "house", "ready"),
        ("017", "BSD/Serpong", 100, 120, 4, 3, 1_600_000_000, "house", "ready"),
        ("018", "BSD/Serpong", 66, 75, 3, 2, 920_000_000, "house", "ready"),
        ("019", "Gading Serpong", 90, 80, 3, 2, 1_250_000_000, "house", "ready"),
        ("020", "Gading Serpong", 72, 70, 3, 2, 1_050_000_000, "house", "ready"),
        ("021", "Gading Serpong", 60, 55, 2, 2, 890_000_000, "house", "ready"),
        ("022", "Gading Serpong", 110, 100, 4, 3, 1_700_000_000, "house", "ready"),
        ("023", "Gading Serpong", 80, 75, 3, 2, 1_150_000_000, "house", "ready"),
        ("024", "Depok", 80, 70, 3, 2, 750_000_000, "house", "ready"),
        ("025", "Depok", 90, 80, 3, 2, 880_000_000, "house", "ready"),
        ("026", "Depok", 60, 50, 2, 1, 520_000_000, "house", "ready"),
        ("027", "Depok", 100, 90, 4, 2, 1_050_000_000, "house", "ready"),
        ("028", "Depok", 70, 60, 2, 2, 640_000_000, "house", "ready"),
        ("029", "Yogyakarta", 90, 70, 3, 2, 650_000_000, "house", "ready"),
        ("030", "Yogyakarta", 80, 60, 2, 2, 540_000_000, "house", "ready"),
        ("031", "Yogyakarta", 110, 90, 4, 3, 820_000_000, "house", "ready"),
        ("032", "Yogyakarta", 70, 55, 2, 1, 480_000_000, "house", "indent"),
        ("033", "Sleman", 100, 80, 3, 2, 885_000_000, "house", "ready"),
        ("034", "Sleman", 85, 70, 3, 2, 720_000_000, "house", "ready"),
        ("035", "Sleman", 120, 100, 4, 3, 1_050_000_000, "house", "ready"),
        ("036", "Bantul", 80, 60, 2, 2, 480_000_000, "house", "ready"),
        ("037", "Bantul", 90, 70, 3, 2, 560_000_000, "house", "ready"),
        ("038", "Bantul", 70, 55, 2, 1, 410_000_000, "house", "ready"),
    ]
    rows = list(fixtures)
    for item in handmade:
        ident, area, land, building, beds, baths, price, ptype, ready = item
        rows.append(
            row(
                f"https://example.test/eval/{ident}",
                price_rp=price,
                land_m2=float(land),
                building_m2=float(building),
                bedrooms=beds,
                bathrooms=baths,
                area=area,
                property_type=ptype,
                readiness=ready,
            )
        )

    key_path = ROOT / "eval" / "answer_key.jsonl"
    key_path.write_text("".join(json.dumps(item) + "\n" for item in rows), encoding="utf-8")

    fixture_path = ROOT / "tests" / "fixtures" / "fields.jsonl"
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text("".join(json.dumps(item) + "\n" for item in fixtures), encoding="utf-8")

    # Sample Run JSON: two true Bintaro Deals in the top 10, one At-Market decoy,
    # and one wrong price so field accuracy is not 1.
    sample = {
        "run_id": "sample",
        "cost_usd": 0.041,
        "duration_s": 39.3,
        "brief": {
            "area": "Bintaro",
            "budget_rp": 1_500_000_000,
            "headroom": 0.05,
            "land_m2": 100,
            "building_m2": 80,
            "bedrooms": 3,
            "soft_tolerance": 0.2,
        },
        "deals": [
            {
                "rank": 1,
                "record": {
                    "url": "https://example.test/eval/001",
                    "portal": "example",
                    "price_rp": 700_000_000,
                    "land_m2": 100,
                    "building_m2": 80,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "area": "Bintaro",
                    "property_type": "house",
                    "readiness": "ready",
                },
            },
            {
                "rank": 2,
                "record": {
                    "url": "https://example.test/eval/004",
                    "portal": "example",
                    "price_rp": 650_000_000,
                    "land_m2": 80,
                    "building_m2": 60,
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "area": "Bintaro",
                    "property_type": "house",
                    "readiness": "ready",
                },
            },
            {
                "rank": 3,
                "record": {
                    "url": "https://example.test/eval/007",
                    "portal": "example",
                    "price_rp": 1_111_000_000,
                    "land_m2": 100,
                    "building_m2": 80,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "area": "Bintaro",
                    "property_type": "house",
                    "readiness": "ready",
                },
            },
        ],
        "records": [],
        "confirmed": 8,
        "quarantined": 1,
        "unreachable": 0,
    }
    sample["records"] = [deal["record"] for deal in sample["deals"]]
    sample_path = ROOT / "tests" / "report" / "sample_run.json"
    sample_path.write_text(json.dumps(sample, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} answer-key rows")


if __name__ == "__main__":
    main()
