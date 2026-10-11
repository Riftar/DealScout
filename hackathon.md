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

### 2026-10-10 (Sat), about 18:20 WIB (integration lane)

Completed:

- `entire session list` showed only this Cursor session. Planning session
  `f35c1e6c-…` was already absent; no `entire clean` needed.
- Commit `1602876`: `.cursor/hooks.json` Entire Cursor hooks wrapped in `cmd.exe`,
  because Cursor's hook runner on this Windows machine has no `sh`.
- Fanned out worktrees from `1602876`, each with `uv sync` and a copied `.env`:
  `../DealScout-collect` (`lane/collect`), `../DealScout-verify` (`lane/verify`),
  `../DealScout-report` (`lane/report`), `../DealScout-ops` (`lane/ops`).
- Started those four lanes. Did not start `content-demo.md`.

Tests run: none new; prior 21 still the baseline on `main`.

Still open: Entire Checkpoints from a git worktree remain untested until a lane
commits. `data/raw/` (tracker export for the collect corpus) is not on disk yet.
### 2026-10-10 (Sat), about 18:30 to 19:15 WIB (collect lane)

Completed:

- `extract/text.py`: `read_text(record, model)` asks the Scout's model for the
  required fields the advert text states. Missing fields are filled with
  `FieldSource.MODEL` and the exact quote; a value the advert does not state
  stays `None`. Quotes for fields structured data already filled go into
  `evidence` so verify can compare (the 99.co 60 m2 vs 62 m2 case). Tests use a
  fake model.
- Structured readers for pinhome, masuksini and idrumah in `extract/structured.py`.
  Fetched one real Listing page of each through `Fetcher` (Snapshots in
  `data/snapshots/`, not committed). pinhome and masuksini expose JSON-LD;
  idrumah exposes a spec table. Land on pinhome is in `og:description`, not
  JSON-LD.
- `collect/corpus.py`: last 14 days, five readable Portals plus OLX, de-duplicated
  by URL. Tests use a tiny fixture CSV. `data/raw/` is still empty.
- `collect/duplicates.py`: `mark_duplicates` sets `duplicate_of` to the first URL
  of the same house (same listing id, or the same Area, sizes, rooms and price).

Structured reader fill of the eight required fields:

| Portal | pages | avg filled |
|---|---|---|
| rumah123 | 9 | 6.00 (land size and Readiness left to advert text) |
| 99.co | 4 | 8.00 |
| pinhome | 1 | 8.00 |
| masuksini | 1 | 8.00 |
| idrumah | 1 | 7.00 (Readiness left to advert text) |

rumah123 and 99.co pages were fetched in the earlier session and live in the
main worktree's Snapshots; this session fetched one page each of pinhome,
masuksini and idrumah.

Tests run: `uv run pytest tests/collect tests/extract`, 26 passed (6 fetcher, 2
corpus, 4 duplicates, 9 structured reader, 5 text read).

Still open: no tracker export in `data/raw/`, so `data/urls/corpus.txt` is not
built. `mark_duplicates` is not wired into the Run (integration owns `run/`).
`read_text` is untested against a live model.

Entire worktree Checkpoint: after commit `6c52ca7` on `lane/collect`,
`entire checkpoint list` reported **0 checkpoints** on this branch. Entire did
not record a Checkpoint from this worktree. Untested no longer: it does not.
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

Entire: commit `02066c4` has no `Entire-Checkpoint:` trailer. Same finding as
collect and report: no Checkpoint from a git worktree. This worktree briefly
checked out `lane/report` before the verify commit was moved onto `lane/verify`.

Still open: Comp size filtering needs a Brief or subject on the `market_price` seam.
### 2026-10-10 (Sat), about 19:10 WIB (report lane)

Completed:

- `report/html.py`: `write_report(shortlist, out_dir)` writes `report.html` and
  `shortlist.json`. Each Deal shows rank, asking price, expected price, how far
  Below Market, the Comps used, and a Dossier (required fields with source and
  quoted words). Quarantined and Unreachable Listings follow with the reason.
  The page is self-contained (inline CSS, no outside assets).
- Held-aside Listings ride on `ReportShortlist` until integration adds them to
  the Shortlist contract (Request in `tasks/report-eval.md`).
- `eval/answer_key.jsonl`: 40 rows, URL and required fields only. Hand-written
  fixture rows plus documented-sample rows; this worktree has no `data/snapshots/`.
- `eval/score.py`: field accuracy, true Deals in the top 10, cost per Run, time
  per Run. Sample Run JSON scores 0.9875 / 10 / 0.012 / 39.3 s. Writes
  `evidence/scores.csv` (ops lane).

Tests run: `uv run pytest tests/report`, 8 passed.

Entire: commit `cbf7555` has no `Entire-Checkpoint:` trailer. Same finding as
collect: Entire did not record a Checkpoint from this worktree.

Still open: 40 rows read from real Snapshots once collect has saved pages;
Shortlist contract still lacks quarantined/unreachable records.
### 2026-10-10 (Sat), about 19:30 WIB (ops lane)

Completed:

- `evidence/`: index mapping `PLAN.md` hard requirements to files; baseline
  before/after notes; neatlogs trace ids; Entire checkpoint list from `main`,
  example Checkpoint link for `2bfc950`, `entire graph stats` and
  `entire graph diff` (scaffold to Run); recovery from `run/graph.py` and
  `tests/run/test_graph.py`; placeholders for #neatHack URLs and neatlogs
  screenshots.
- `docs/business-plan/unit_economics.csv`: wall time and token counts from
  `hackathon.md`; USD row pending neatlogs export.
- `deploy/README.md` and `deploy/run-scheduled.sh` for scheduled EC2 Runs.

Tests run: none (ops lane is evidence and deploy docs only).

Still open: after lane merges, complete before/after numbers, `evidence/scores.csv`,
live recovery neatlogs trace, cfo.ai export, public post URLs.

### 2026-10-10 (Sat), about 19:35 WIB (integration lane)

Completed:

- Merged into `main`: `lane/collect` (`413af59`), `lane/verify` (`0c8a52d`),
  `lane/report` (`b3ea590`), `lane/ops` (`f68d670`). `lane/content` not merged.
- `run/seams.py` now resolves real modules for text read, checks, Verifier, Arbiter,
  value, and report on `main`.

Tests run: `uv run pytest`, 90 passed.

Still open: re-run seed URLs for a traced after Run and update `evidence/before-after.md`;
`data/urls/corpus.txt` when `data/raw/` exists; Shortlist contract for Quarantined and
Unreachable records (report `ReportShortlist` workaround).

### 2026-10-10 (Sat), about 19:45 WIB (integration lane)

Completed:

- Shortlist contract carries `quarantined_listings` and `unreachable_listings`; the
  Rank step attaches them so `write_report` lists each with its reason.
- Extract and Recover call `mark_duplicates`. A Duplicate is Confirmed but is not a
  Comp and not a Deal.
- `market_price(..., brief=None)`: when the Brief states land or building size, Comps
  outside `soft_tolerance` are dropped. Indent Listings stay out.

Tests run: `uv run pytest`, 94 passed.

Still open: corpus when `data/raw/` exists.

### 2026-10-10 (Sat), about 21:13 WIB (integration lane, live after Run)

Completed:

- Re-ran the seed Brief after switching the LLM provider. Previous attempt hung
  (~25 min, no output); killed it. `ArbiterCall.value` now accepts a JSON
  number as a string so a price like 875000000 does not crash Recover.
- Live Run: `uv run dealscout run --area Bintaro --budget 1500000000 --urls data/urls/seed.txt`
  - wall 318.4 s, neatlogs flush ok
  - trace `4f93ea5781bc955312fabdaf1cf1b111`
  - Plan tokens 87 (prompt 49, completion 38); other steps are not in that count
  - confirmed=3 quarantined=9 unreachable=0 deals=0
  - report `data/runs/20261010T211307Z/report.html` (local)

Tests run this session: `uv run pytest tests/verify tests/run tests/extract`, 53 passed.
Full suite not re-run after the last Recover try/except.

Still open: no Deal on this seed; Confirmed Listings that are not Deals are
missing from `shortlist.json` `records`; total tokens across Scout/Verifier/Arbiter.

### 2026-10-10 (Sat), content lane, posters

Completed:

- `content/posters/`: three 1600 x 900 images for X posts, each an HTML page with a shared
  stylesheet, rendered to PNG by `render.sh` (headless Edge). A first set was committed
  before the builder saw it; this set replaces it with plainer wording and no name.
  - `what-it-does`: describe the house, get the listings priced below market, with proof.
  - `two-sizes`: the 99.co Disagreement from the 17:05 entry, 60 m2 against 62 m2.
  - `ninety-in-a-hundred`: 90 of 100 sampled rows missing a size, from "Problem" above
    (10 had both).
- `content/posts.md`: one caption and alt text per poster.
- Every number is from this file. Each header says "In build", because the checks and the
  Valuation do not exist yet.
- New rule in `AGENTS.md`: nothing under `content/` is committed before the builder says yes.

Tests run: none; the content lane has no tests. Each PNG was checked at 1600 x 900 by eye.

The builder approved this set and its captions in the chat before the commit. The font is
Bricolage Grotesque, picked by the builder from three samples.

Still open: the fonts load from Google Fonts at render time, so `render.sh` needs a network
connection. The rule and `DESIGN.md` are on `main`.

### 2026-10-11 (Sun), about 01:45 to 02:35 WIB (integration lane, Dashboard and Jobs)

Brought the code in line with the glossary change of 22:27 (`CONTEXT.md`, ADR 0001): a buyer
now works through a Dashboard and saved Jobs, where before there was one hard-coded Brief in
a cron script.

Completed:

- `domain/job.py`: contracts for Job (Brief, Portals from a fixed list of six, daily time in
  Asia/Jakarta), JobRun, and the Listing list with its rows.
- `dashboard/store.py`: Jobs and Runs in `data/state/jobs.sqlite`. A daily Run is queued at
  most once per Job per date, and only one Run goes at a time, so one Fetcher keeps one
  crawl delay per Portal.
- `dashboard/schedule.py` and `dealscout tick`: queue the Jobs whose time has come, carry
  out one queued Run, save its Listing list. Cron calls it every minute. A Job made after
  today's time first fires tomorrow. A Job's Listing URLs are the `data/urls/*.txt` rows on
  its Portals.
- `dashboard/listing_list.py`: Confirmed Listings in the Brief's Area at or under budget
  plus Headroom, ordered by Valuation ratio, with over-budget marked. No ratio when there
  are fewer than three Comps or the typed Area did not map. Quarantined and Unreachable
  Listings are listed with their reason.
- `dashboard/app.py`, `pages.py` and `dealscout dashboard`: define a Job, change it, Run
  now, stop daily Runs, read the Listing list. A Brief change shows a warning, then makes a
  new Job; the old one keeps its list and stops firing. Styled from `DESIGN.md`.
- The Dashboard reads only the Job store. A Listing list carries confirmed numbers, the
  Portal's Listing id and a link; no title, description or quoted page text.
- `deploy/`: systemd unit, nginx site, cron entry and `tick.sh`, which replaces
  `run-scheduled.sh`. Written by the integration lane because no ops session was open.
- `run/cli.py`: the traced Run moved into `execute_run`, shared by `run` and `tick`.

Tests run: `uv run pytest`, 151 passed (48 new: `tests/dashboard/`, `tests/domain/test_job.py`).
The Dashboard was also served locally and checked in a browser and with curl: define a Job,
a rejected form, the Brief-change warning, a 413 on an oversized body.

Still open:

- No Job has run with live models, and nothing is deployed. The tick was tested with a
  stand-in for the Run.
- The site has no accounts: anyone with the URL can define a Job. Spend is held by limits
  (20 active Jobs, three Run now per Job per day, one Run at a time, nginx write rate).
- `data/urls/seed.txt` holds 12 URLs on two Portals, so a Job on the other four finds none
  and its Run fails with that reason.
- Each Run fetches its pages again; price history across Runs is not kept.

### 2026-10-11 (Sun), about 16:30 to 17:30 WIB (integration lane, Dashboard tested live)

Tested the Dashboard, Jobs and the tick on the builder's machine against a scratch Job
store, with the Dashboard served locally and a script calling `dealscout tick` once a
minute in place of cron.

Measured:

- First try, 16:33: "Run now" started a Run at once. It failed in under a minute because
  the model endpoint answered 422, budget exceeded. The Job page showed "the Run failed
  (UnprocessableEntityError)" and the detail stayed in the tick log.
- Daily time: a Job set to 16:35 WIB was fired by the first tick after 16:35 and by no
  later tick. It was on a Portal with no URLs on file, and its Run failed with that reason.
- Run with the model steps switched off, 16:37: 37 seconds, 12 pages fetched, confirmed=4
  quarantined=8. The four Confirmed were in other Areas than the Brief's, so no Listing
  fit and there were no Comps.
- Run with live models after the builder changed the model, 16:45 to 17:16: 31 minutes,
  confirmed=0 quarantined=12 unreachable=0, trace `3b5428047b812762979cdab6b61ca1e5`.
  Five minutes went on plan, fetch, read and Check; 26 on the recover step. Twenty ticks
  ran meanwhile and none started a second Run.
- For comparison, the Run of 10 Oct on the earlier model: 318.4 s, confirmed=3
  quarantined=9 on the same 12 URLs (`evidence/before-after.md`).
- No phone number or WhatsApp link on the Job pages. The form fits a 375 px screen.

Tests run: `uv run pytest`, 151 passed.

Still open:

- The newer model Confirmed nothing. Reasons on the list are Verifier Disagreements on land
  size, building size, bedrooms and Readiness, including on the four 99.co Listings that
  pass the Checks with no model. Not yet investigated.
- A Valuation ratio on a Job page has only been seen with made-up records, because no live
  Run has produced three Comps in one Area.
- Nothing is deployed. The systemd unit, nginx site and cron entry have not run on an
  instance.

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
