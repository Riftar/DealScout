# Recovery when a fetch or check fails

DealScout never drops a Listing silently. The Recover step (`run/graph.py`) runs
after Check:

1. **Failed fetch:** re-fetch once, then mark **Unreachable** with the reason.
2. **Failed check:** Scout re-extracts with the failure as feedback (once), then
   **Quarantine** with the reason.

## Automated proof (no Portal call)

`tests/run/test_graph.py` on fakes:

- `test_run_end_to_end_on_fakes`: first fetch of one URL fails; second fetch in
  Recover succeeds; Run finishes with `unreachable=0` and four Confirmed.
- `test_unreachable_after_one_retry`: fetch still fails after one retry;
  Listing is Unreachable and fetch was attempted twice.

Run: `uv run pytest tests/run/test_graph.py -k unreachable`

## neatlogs trace (pending)

Ops will attach a `dealscout-run` trace id here after a live Run where a fetch
fails (for example a blocked or bad URL) and Recover completes. Baseline Run had
`unreachable=0` on the seed file.
