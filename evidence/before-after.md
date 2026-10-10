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

## After (live Scout + Verifier + Arbiter on `main`)

Same Brief and URL file, 10 Oct 2026 ~21:13 WIB:

| Metric | Value |
|---|---|
| neatlogs trace | `4f93ea5781bc955312fabdaf1cf1b111` |
| Wall time | 318.4 s |
| Tokens (Plan model only) | 87 (prompt 49, completion 38) |
| Confirmed | 3 |
| Quarantined | 9 |
| Unreachable | 0 |
| Deals | 0 |
| neatlogs flush | ok |

Report: `data/runs/20261010T211307Z/report.html` (local). Quarantine reasons
were mostly Scout vs Verifier price/size disagreements and missing land size.
None of the three Confirmed Listings became a Deal (Area, budget ceiling, and
Below Market all have to hold).

`eval/score.py` was not used for this pair: `eval/answer_key.jsonl` is fixture
URLs, not the live seed list, so field accuracy against that key is not a
comparison of the two Runs.
