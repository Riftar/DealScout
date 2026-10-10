# DealScout: neatHack build log

## Project

- Name: DealScout
- Purpose: an agent that finds the listings that beat the going price for the house a buyer
  describes, and proves each one from its source page.
- Problem: listing data gathered automatically is often misread, and the cheapest-looking
  listing is often the misread one. The builder's own tracker of about 4,990 Indonesian
  house listings shows it: in 100 rows sampled from the later part, 10 had both land and
  building size.

## Team

- Riftar (solo)

## Stack

In use:

- Claude Code as the coding agent.

Planned, not yet in use:

- neatlogs: a trace for every Run, Detection rules, before/after comparison.
- Entire: Checkpoints on agent commits, entire-graph.
- cfo.ai: the business plan (pricing, costs, revenue, runway).
- AWS EC2: scheduled Runs and report hosting.
- Python 3.12, uv, LangGraph, an OpenAI-compatible model endpoint.

## Build log

### 2026-10-10 (Sat), planning session, about 15:30 to 16:45 WIB

Completed:

- Read the published rules and all eleven FAQ answers at neatlogs.com/hackathon, and the
  neatHack skill.
- Agreed scope and vocabulary with the builder in a question-and-answer session. Results
  are in `PLAN.md` and `CONTEXT.md`.
- Sampled about 170 rows of the builder's listings tracker (about 4,990 rows, 9 Jun to
  9 Oct 2026). Findings are in `PLAN.md`.
- Fetch test: one plain request to one listing page on each of six portals, and a read of
  each robots.txt. Five returned full pages; OLX returned an empty shell.
- Wrote `PLAN.md`, `CONTEXT.md`, `AGENTS.md`, `.gitignore` (checked against 21 sample
  paths) and `.gitattributes`.
- Created this repository.

Tests run: none. No code exists yet.

- Enabled Entire (CLI 0.11.4) for Claude Code in this repo. Pushing session logs is off
  until the builder decides whether agent transcripts go public.

Open at the end of the session:

- Entire is not logged in. `entire checkpoint list` shows 0 Checkpoints: the planning
  session began before Entire's hooks existed, so its commits are not linked. The next
  session, started inside this repo, is the first that can be.
- The neatlogs CLI is not installed and no trace has been sent.
- Whether Entire records Checkpoints from a git worktree is untested.
- No portal has been tested from an AWS address. Lamudi and jualrumahjakarta are untested.

### 2026-10-10 (Sat), about 16:45 to 16:55 WIB

Completed:

- Entire: the builder logged in and installed the graph plugin (v0.4.0). Ran
  `entire graph init-agents`, which wrote `.entire/graph-agent.md` and a pointer in
  `AGENTS.md`.
- Enabled Entire for Cursor and OpenCode as well as Claude Code, because other lanes may
  run in those tools. Pushing session logs is still off.
- Removed an accidental Entire install from the builder's home folder. It is unrelated to
  this repo.

Tests run: none. No code exists yet.

Still open: no Checkpoint recorded, no neatlogs trace, no `.env`.

### 2026-10-10 (Sat), about 16:55 to 17:05 WIB

Completed:

- First Entire Checkpoint recorded and linked to commit `4bf3ad7`
  (`Entire-Checkpoint: 01M4JKN6GFF8GTDVFZFGQF4XH2`).
- Found that Entire's commit hook waits for a terminal answer and hangs an agent's commit.
  Setting `ENTIRE_TEST_TTY=0` avoids it; the rule is in `AGENTS.md`.
- Project scaffold: `pyproject.toml`, `uv.lock`, Python 3.12.14, neatlogs SDK 1.4.26.
- Contracts in `src/dealscout/domain/`: Brief, Listing, Snapshot, Listing Record,
  Disagreement, Market Price, Valuation, Deal, Shortlist.
- neatlogs CLI 0.2.0 installed by the builder; profile `work` set. Not logged in yet.

Tests run: `uv run pytest`, 5 passed (contracts only).

Still open: no neatlogs trace, no `.env`, no model endpoint checked, worktree Checkpoints
untested.

### 2026-10-10 (Sat), about 17:00 to 17:05 WIB

Completed:

- neatlogs CLI logged in (device flow); one project found.
- Setup check `python -m dealscout.run.smoke`: both configured models returned the expected
  tool call (3.1 s and 4.5 s), and the trace reached neatlogs: workflow `dealscout-smoke`,
  trace `99136eadf37cbd8e9c3c77da929fc23d`, status OK, 5,549 tokens.

Tests run: `uv run pytest`, 5 passed. The smoke check is run by hand, not by pytest.

Still open: worktree Checkpoints untested; no Listing read yet.

### 2026-10-10 (Sat), about 17:05 to 17:20 WIB

Completed:

- `collect/fetcher.py`: plain requests, robots.txt and crawl delay honoured, each page saved
  as a Snapshot, unusable pages returned as Unreachable with the reason.
- Fetched two real Listings through it (rumah123 and 99.co), both 200 with about 600 KB.
- Finding on the first 99.co page: the Portal's own data says building 60 m2 and
  electricity 0 W, while the advert text says 62 m2 and 2,200 W; the URL says "1miliar" and
  the price is Rp 1.1 billion. This is the kind of Disagreement the Verifier is for.
- `data/urls/seed.txt`: 12 Listing URLs for the first slice.

Tests run: `uv run pytest`, 11 passed (5 contracts, 6 fetcher).

### 2026-10-10 (Sat), about 17:20 to 17:35 WIB

Completed:

- `extract/structured.py`: reads a Snapshot's own structured data into a Listing Record, in
  code, for rumah123 and 99.co. A zero or blank counts as not stated.
- `domain/areas.py`: the seven Areas and the names Portals use for them.
- Run on the two real Snapshots: the 99.co page stated all eight required fields; the
  rumah123 page stated six and left land size and Readiness to the advert text.

Tests run: `uv run pytest`, 17 passed (5 contracts, 6 fetcher, 6 structured reader). The
reader tests use hand-written pages, not copies of real adverts.

### 2026-10-10 (Sat), about 17:35 to 17:55 WIB

Completed:

- Task briefs for every lane in `tasks/`, with the function signatures between lanes in
  `tasks/README.md`, so new sessions can continue without this one.
- Valuation formula and thresholds written into `PLAN.md` "Decisions".
- Entire: session transcripts are pushed from the next session on. The planning and setup
  session stays local by the builder's choice; its Checkpoint ids remain in earlier commit
  messages but have no public session behind them.

Tests run: `uv run pytest`, 17 passed.

Still open: no model reads the advert text yet; no Extraction Checks; pinhome, masuksini and
idrumah have no structured reader.

Planned next:

- One Listing end to end: fetch, Snapshot, structured read, Extraction Checks.

### 2026-10-10 (Sat), about 17:25 to 17:40 WIB (integration lane)

Completed:

- `run/llm.py`: `scout_model()` from `LLM_MODEL_FAST`, `verifier_model()` from
  `LLM_MODEL_STRONG`.
- `run/graph.py`: one Run as a LangGraph graph (Plan → Collect → Extract → Check →
  Recover → Value → Rank → Report) with a SQLite checkpointer in `data/state/`.
- `run/fakes.py` and `run/seams.py`: fakes for `read_text`, checks, Verifier, Arbiter,
  Market Price, Valuation, Shortlist and `write_report` until those lanes merge.
- Recover: one retry on a failed fetch or failed check, then Unreachable or Quarantined
  with the reason. The Run always finishes.
- `run/cli.py`: `dealscout run --area Bintaro --budget 1500000000 --urls data/urls/seed.txt`.
- neatlogs: workflow `dealscout-run`, one `neatlogs.trace` per Run, LangChain handler on
  `graph.invoke`, flush at the end.
- Entire: this session is on `main` (integration owns it), not a worktree.
  `entire checkpoint list` before the commit showed another Cursor session's temporary
  Checkpoint on `main`; planning session `f35c1e6c-…` was already absent.

Live Run over `data/urls/seed.txt` (12 URLs, Bintaro, budget Rp 1.5e9):

- wall time 39.3 s
- tokens 2,649 (prompt 2,572, completion 77) from the Plan model call
- neatlogs trace id `1d5e860da95bc00cac30b0b554a9860a`, flush ok
- result: confirmed=8, quarantined=4, unreachable=0, deals=0 (Market Price needs three
  Comps in the Brief's Area; the seed mix and fake text-read leave too few Confirmed
  Bintaro rows Below Market)

Tests run: `uv run pytest`, 21 passed (17 prior + 4 `tests/run` end-to-end on fakes,
including resume after Collect).

Still open: real `read_text`, Extraction Checks, Verifier, Arbiter, value and report
lanes; deals on a live Run once those land and Comps thicken.

### 2026-10-10 (Sat), about 19:20 WIB (verify lane)

Completed:

- `verify/checks.py`: `run_checks` in code (required missing, room counts, size and
  price bands, URL/title price drift, not a house, structured vs advert text).
- `verify/verifier.py` and `verify/arbiter.py`: strong-model Verifier reads the
  Snapshot without the Scout's values; Arbiter settles Disagreements from a page
  quote or Quarantines.
- `value/market.py` and `value/valuation.py`: Market Price, Valuation, Shortlist
  (Below / At / Above Market, Split, soft misses on Deals). Indent Listings are not
  Comps.

Tests run: `uv run pytest tests/verify tests/value`, 47 passed.

Entire: will log Checkpoint after commit (worktree was wrongly on `lane/report`
briefly; committed from `lane/verify`).

Still open: Comp size filtering needs a Brief or subject on the `market_price` seam.

## Demo

Not available yet.

## Known limitations and next steps

- Market Price comes from asking prices, not sale prices.
- OLX pages cannot be read with a plain request; those Listings will be reported as
  Unreachable.

## Submission

Confirmed from the published page on 10 Oct 2026:

- Window: Mon 12 Oct, 7:00 to 11:55 PM IST (20:30 WIB to 01:25 WIB on Tue 13 Oct).
- Form: a public quote post of the official neatlogs submission post on X, with team, name,
  project, public repository and demo link.
- Demo video of three minutes or less, covering architecture, implementation, runtime,
  reasoning and result for each of neatlogs, Entire and cfo.ai.
- Public repository with commits dated inside the hackathon, with supporting evidence.
- The cfo.ai business plan included in the submission.

Outstanding: all of the above.
