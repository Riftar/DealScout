# Task briefs

One brief per piece of work. Pick the brief for your lane, read `AGENTS.md` and `CONTEXT.md`
first, and write your dated entry in `hackathon.md` when you finish.

## State on Sat 10 Oct, 19:45 WIB

On `main`, with **94 tests** passing (`uv run pytest`):

- `domain/`, `run/`: contracts and LangGraph Run; seams now load real collect, verify,
  value and report modules when present (no fakes for those steps on `main`).
- `collect/`, `extract/`: fetcher, corpus, duplicates, structured readers (six
  Portals), Scout `read_text`.
- `verify/`, `value/`: Extraction Checks, Verifier, Arbiter, Market Price, Valuation,
  Shortlist.
- `report/`, `eval/`: `write_report`, answer key, `eval/score.py`.
- `evidence/`, `deploy/`, `docs/business-plan/`: ops lane artifacts on `main`.
- Before/after pair is in `evidence/before-after.md` (fakes vs live models on the
  same seed Brief). After: 318.4 s, confirmed=3 quarantined=9 deals=0,
  trace `4f93ea5781bc955312fabdaf1cf1b111`.
- Shortlist carries Quarantined and Unreachable records. Duplicates are marked after
  extract. Comps follow Brief size when the Brief states it.

Merged: collect, verify, report, ops, and content posters (`cb9bd87`). Content
copy still waits for Sunday numbers.

## Order

| Brief | Lane | Starts | Needs |
|---|---|---|---|
| `integration-run.md` | integration | done | merges from lane branches |
| `collect-extract.md` | collect | merged | — |
| `verify-value.md` | verify | merged | — |
| `report-eval.md` | report | merged | — |
| `ops-evidence.md` | ops | merged | after numbers: before/after, scores.csv |
| `content-demo.md` | content | Sunday | numbers in `evidence/` |

At most three coder lanes run at once. The integration lane merges.

## Starting a lane session

```bash
git worktree add ../DealScout-<lane> -b lane/<lane>
cd ../DealScout-<lane>
uv sync
cp ../DealScout/.env .env
```

Then start the agent inside that folder. The first lane session checks that
`entire checkpoint list` shows its commit, and logs the result in `hackathon.md`: Entire in
a worktree is untested.

## First session after the handoff

Run `entire session list`. If it shows session `f35c1e6c-efae-4b66-92c0-7e2bc1b92deb` (the
planning session, kept private by the builder), remove it before your first commit:

```bash
entire clean --session f35c1e6c-efae-4b66-92c0-7e2bc1b92deb --force
```

## Sessions are public

Entire pushes each session's transcript with `git push`, and the repo is public. Keep keys,
passwords and personal details out of the chat. `.env` holds the keys; code loads it at run
time with `load_dotenv(".env")`.

## The seams between lanes

Each lane builds to these signatures so the Run can call them. All types are in
`dealscout.domain`.

```python
# collect
Fetcher(snapshot_dir).fetch(url: str) -> Snapshot
# extract
read_structured(html: str, url: str, portal: str) -> ListingRecord
read_text(record: ListingRecord, model) -> ListingRecord           # the Scout's read
# verify
run_checks(record: ListingRecord) -> list[CheckFailure]
verify(record: ListingRecord, html: str, model) -> list[Disagreement]   # the Verifier
arbitrate(record, disagreements, html: str, model) -> ListingRecord     # the Arbiter
# value
market_price(area: str, confirmed: list[ListingRecord], brief: Brief | None = None) -> MarketPrice | None
value(record: ListingRecord, market: MarketPrice) -> Valuation
shortlist(brief: Brief, confirmed: list[ListingRecord]) -> Shortlist
# report
write_report(shortlist: Shortlist, out_dir: Path) -> Path
```

`model` is a LangChain chat model built by `dealscout.run.llm` (integration lane). Lanes
take it as an argument and test with a fake.
