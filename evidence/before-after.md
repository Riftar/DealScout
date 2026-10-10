# Before / after Run pair

PLAN.md asks for a before/after pair with numbers compared. Same Brief and URL
list, replayed after agent fixes land in `main`.

## Before (baseline on `main`, fakes for verify/value/report)

Measured live Run, 10 Oct 2026 (`hackathon.md`, integration lane):

| Metric | Value |
|---|---|
| neatlogs trace | `1d5e860da95bc00cac30b0b554a9860a` |
| Wall time | 39.3 s |
| Tokens (Plan model) | 2,649 (prompt 2,572, completion 77) |
| Confirmed | 8 |
| Quarantined | 4 |
| Unreachable | 0 |
| Deals | 0 |

Brief: Bintaro, budget Rp 1.5e9, URLs `data/urls/seed.txt` (12 listings).

## After (pending)

After collect, verify, and report merge into `main`, re-run the same Brief and
URL file, flush a new neatlogs trace, and score with `eval/score.py` against
`eval/answer_key.jsonl` (report lane). Append a row to `evidence/scores.csv`.

Compare field accuracy, true Deals in the top 10, cost per Run, and time per Run
from the scorer output.
