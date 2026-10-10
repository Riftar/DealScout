# Task briefs

One brief per piece of work. Pick the brief for your lane, read `AGENTS.md` and `CONTEXT.md`
first, and write your dated entry in `hackathon.md` when you finish.

## State on Sat 10 Oct, 17:45 WIB

On `main`, with 17 tests passing (`uv run pytest`):

- `domain/`: the contracts, and the seven Areas with the names Portals use for them.
- `collect/fetcher.py`: `Fetcher(snapshot_dir).fetch(url) -> Snapshot`.
- `extract/structured.py`: `read_structured(html, url, portal) -> ListingRecord`, for
  rumah123 and 99.co.
- `run/smoke.py`: checks both models can call a tool and that a trace reaches neatlogs.
- `data/urls/seed.txt`: 12 Listing URLs.

Nothing else exists yet: no model reads advert text, no Extraction Checks, no Verifier, no
Valuation, no report, no Run.

## Order

| Brief | Lane | Starts | Needs |
|---|---|---|---|
| `integration-run.md` | integration | now | fakes for the other lanes until they merge |
| `collect-extract.md` | collect | now | nothing |
| `verify-value.md` | verify | now | nothing |
| `report-eval.md` | report | now | hand-made `Shortlist` objects until a Run exists |
| `ops-evidence.md` | ops | after the first traced Run | a Run on `main` |
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
