"""eval/score.py against the answer key and a sample Run JSON."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "eval"
KEY = EVAL / "answer_key.jsonl"
SAMPLE = EVAL / "sample_run.json"
SCORE = EVAL / "score.py"


def test_answer_key_has_about_forty_rows_of_url_and_fields():
    rows = []
    for line in KEY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        rows.append(row)
        assert set(row) <= {
            "url",
            "price_rp",
            "land_m2",
            "building_m2",
            "bedrooms",
            "bathrooms",
            "area",
            "property_type",
            "readiness",
        }
        assert "url" in row
        assert "name" not in row
        assert "phone" not in row
        assert "email" not in row
    assert 38 <= len(rows) <= 45
    assert len({row["url"] for row in rows}) == len(rows)


def test_score_py_on_sample_run_prints_four_numbers(tmp_path: Path):
    out_csv = tmp_path / "scores.csv"
    result = subprocess.run(
        [sys.executable, str(SCORE), str(SAMPLE), "--out", str(out_csv)],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    printed = dict(line.split("=", 1) for line in lines)
    assert set(printed) == {
        "field_accuracy",
        "true_deals_in_top_10",
        "cost_per_run",
        "time_per_run",
    }
    accuracy = float(printed["field_accuracy"])
    assert 0.0 <= accuracy <= 1.0
    assert int(printed["true_deals_in_top_10"]) >= 0
    assert float(printed["cost_per_run"]) == 0.012
    assert float(printed["time_per_run"]) == 39.3
    assert accuracy == 0.9875
    assert int(printed["true_deals_in_top_10"]) == 10
    csv_text = out_csv.read_text(encoding="utf-8")
    assert "field_accuracy" in csv_text
    assert "0.9875" in csv_text
    assert re.search(r"true_deals_in_top_10", csv_text)
