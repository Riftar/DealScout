# Report and eval

Lane: report. Branch: `lane/report`. Writes `src/dealscout/report/`, `eval/`,
`tests/report/`.

## Build

1. `report/html.py`: `write_report(shortlist, out_dir) -> Path`. One static HTML file and a
   JSON file beside it. For each Deal: rank, asking price, expected price, how far Below
   Market, the Comps used, and a Dossier showing each required field with its source and
   the quoted words from the page. Then the Quarantined and Unreachable Listings with the
   reason for each. Everything the page needs is inside the file.
2. `eval/answer_key.jsonl`: about 40 Snapshots with the correct required fields, read by
   hand from the saved pages. Store URL and field values only.
3. `eval/score.py`: scores a Run's JSON against the answer key: field accuracy, how many
   true Deals are in the top 10, cost per Run and time per Run. Writes one row per Run to
   `evidence/scores.csv`.

## Done

- `uv run pytest tests/report` passes.
- `write_report` on a hand-made `Shortlist` produces a page that opens from disk.
- `eval/score.py` runs on a sample Run JSON and prints the four numbers.

## Requests

- ops lane: `eval/score.py` writes `evidence/scores.csv`.
