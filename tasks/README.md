# Task briefs

One brief per piece of work. Pick the brief for your lane, read `AGENTS.md` and `CONTEXT.md`
first, and write your dated entry in `hackathon.md` when you finish.

## State on Sat 10 Oct, 18:25 WIB

On `main` at `1602876`, with 21 tests passing (`uv run pytest`):

- `domain/`: the contracts, and the seven Areas with the names Portals use for them.
- `collect/fetcher.py`: `Fetcher(snapshot_dir).fetch(url) -> Snapshot`.
- `extract/structured.py`: `read_structured(html, url, portal) -> ListingRecord`, for
  rumah123 and 99.co.
- `run/`: LangGraph Run with SQLite checkpointer, CLI, llm client, neatlogs, and fakes
  for the other lanes. Live Run over `data/urls/seed.txt` traced (see `hackathon.md`):
  39.3s, 2,649 tokens, neatlogs `1d5e860da95bc00cac30b0b554a9860a`, confirmed=8,
  quarantined=4, unreachable=0, deals=0.
- `run/smoke.py`: checks both models can call a tool and that a trace reaches neatlogs.
- `data/urls/seed.txt`: 12 Listing URLs.
- `.cursor/hooks.json`: Entire Cursor hooks wrapped in `cmd.exe` so they run on Windows.

Lanes started in worktrees from `1602876` (not yet merged):

| Brief | Lane | Worktree | Branch |
|---|---|---|---|
| `collect-extract.md` | collect | `../DealScout-collect` | `lane/collect` |
| `verify-value.md` | verify | `../DealScout-verify` | `lane/verify` |
| `report-eval.md` | report | `../DealScout-report` | `lane/report` |
| `ops-evidence.md` | ops | `../DealScout-ops` | `lane/ops` |

Not started: `content-demo.md` (Sunday). Do not start it.

Still missing real modules: model text read, Extraction Checks, Verifier, Arbiter,
Valuation package, report. The Run calls fakes for those until their lanes merge.

## Order

| Brief | Lane | Starts | Needs |
|---|---|---|---|
| `integration-run.md` | integration | done (`2bfc950`) | fakes for the other lanes until they merge |
| `collect-extract.md` | collect | in progress | nothing |
| `verify-value.md` | verify | in progress | nothing |
| `report-eval.md` | report | in progress | hand-made `Shortlist` objects until a Run exists |
| `ops-evidence.md` | ops | in progress | first traced Run is on `main` |
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
market_price(area: str, confirmed: list[ListingRecord]) -> MarketPrice | None
value(record: ListingRecord, market: MarketPrice) -> Valuation
shortlist(brief: Brief, confirmed: list[ListingRecord]) -> Shortlist
# report
write_report(shortlist: Shortlist, out_dir: Path) -> Path
```

`model` is a LangChain chat model built by `dealscout.run.llm` (integration lane). Lanes
take it as an argument and test with a fake.
