# DealScout plan

Agreed Sat 10 Oct 2026, 16:45 WIB, at the end of the planning session. Changes after that
are logged in `hackathon.md`.

## What it is

An agent that takes a buyer's Brief (area, budget, size), collects listings from Indonesian
property portals, checks its own reading of every listing against the source page, values
each one against area comps, and returns a Shortlist of Deals with the evidence attached.

A buyer reaches it through the Dashboard, a public website on AWS. There they save a Job:
one Brief, Portals picked from a fixed list, and a daily time in Asia/Jakarta. Each firing
of a Job is a Run, and the Job's page shows the Listing list from its latest Run. Added
Sat 10 Oct, 22:27 WIB (`docs/adr/0001-buyer-jobs-on-aws.md`).

The thesis: in a deal screen, the listing that looks cheapest is often the one the agent
misread. So DealScout spends its verification effort at the top of its own ranking, and
never recommends a listing whose numbers it could not confirm on the source page.

Clean-room: every line is written during the hackathon. Nothing is copied from or refers to
earlier projects. The 60-row seed CSV and the Google Sheet are input data only.

## What the real data shows

Read from the "Property Listings Tracker" Sheet on 10 Oct. Counts are from the grid; the
quality notes come from about 50 sampled rows, not a full scan.

- About 4,990 listing rows, 9 Jun to 9 Oct 2026. The 9 Oct batch is 87 rows.
- Eight portals: 99.co, rumah123, OLX, Lamudi, pinhome, masuksini, idrumah,
  jualrumahjakarta.
- Asking prices in the samples sit at or under about Rp 1.15 Miliar, across BSD/Serpong,
  Gading Serpong, Bintaro, Depok, Yogyakarta, Sleman and Bantul.

Failures seen in the samples, which become the agent's Extraction Checks:

- Size fields blank although the page text states them (all 11 sampled rows of the 9 Oct
  batch have no land or building size, so none can be valued).
- Columns shifted or swapped in recent rows: description in the location column, a
  thumbnail URL where the numeric price belongs.
- Price disagreement inside one row: "Rp 270,000,000" shown, 299000000 stored.
- A price that cannot be right: a 178 m2 house in Bintaro Jaya at Rp 165 Juta, which the
  earlier process itself tagged "mohon verifikasi".
- Truncated values (electricity 200 or 300 W), bathroom counts of 7 on a 63 m2 house.
- The same house listed twice under different URLs.
- Area names fragmented ("BSD", "BSD/Serpong", "BSD Tangerang", "BSD City") and
  sub-areas filed under the wrong parent, which thins and skews the comps.

Fetch test from this machine, 10 Oct, one polite plain request per portal:

| Portal | Listing page | robots.txt for a generic client |
|---|---|---|
| rumah123 | 200, full HTML, JSON-LD present | Listing pages allowed, filtered search disallowed, crawl delay 5 s |
| 99.co | 200, full HTML, JSON-LD present | Listing pages allowed, filtered search disallowed |
| pinhome | 200, full HTML, JSON-LD present | Listing pages allowed, sitemaps published |
| masuksini | 200, full HTML, JSON-LD present | Listing pages allowed, filtered search disallowed |
| idrumah | 200, full HTML | No blocking rule seen |
| OLX | 200 but an empty 2 KB shell | Item pages allowed, content needs a browser |

Not tested: Lamudi, jualrumahjakarta, and any of them from an AWS address.

## Listing Record fields

The Sheet's 26 columns, evaluated against about 170 sampled rows. The Record is rebuilt
around what a Valuation needs and what can be confirmed on the page.

Must be Confirmed before a Listing is ranked or used as a Comp:

| Field | Replaces | Note |
|---|---|---|
| url, listing id, Portal | url, source | Portal comes from the URL. The portal's own id is the identity across Runs. |
| price (whole Rupiah) | price_rp, price_numeric | One number plus the text it was read from. The Sheet holds at least six display formats, and the numeric column later holds thumbnail URLs. |
| land size, building size | lt_m2, lb_m2 | Sampled cells hold "125", "85 m2", "84 m²" and leaked `{'value': '62', 'unit': 'm2'}` strings. Blank in most sampled rows since September. |
| bedrooms, bathrooms | kt, km | Sampled rows include bathroom counts of 89 and 205, copied from land size. |
| Area | area | Canonical, one per Listing. |
| property type | new | A boarding house ("kosan") sits in the data as a house. It must not be a Comp. |
| Readiness | status, furnish_status | Ready or Indent. "Siap huni" is readiness, not furnishing. |

Kept when the page states them: title and location text (split out of detail_location),
estate name (cluster), floors, certificate, furnishing, previous price, one thumbnail.

Tracked by DealScout rather than read from the page: first seen, last seen, price history,
listing status, record status with its reason, duplicate-of, and the Snapshot each value
came from.

Dropped:

- The three valuation columns. A Valuation belongs to a Run and its Comps, not to the Listing.
- highlights. It is a summary; the report writes its own from Confirmed fields.
- year_built and price_change: blank in all 120 rows sampled for them. The previous price
  is on the page (rumah123 exposes it) and is read from there instead.
- hook_corner: blank in nearly every sampled row.
- nearby_station: the constant "KRL" on 99.co rows, fragments elsewhere.
- electricity_w: values such as 200 and 300 where 2200 and 1300 are meant.

## Hard requirements

From neatlogs.com/hackathon and its FAQ, read 10 Oct 2026.

- Window: Sat 10 Oct 14:00 WIB to the submission deadline. All code written inside it.
- Submit: Mon 12 Oct 20:30 WIB to Tue 13 Oct 01:25 WIB (7:00-11:55 PM IST), as a public
  quote post of the official neatlogs post on X, with team, name, project, public repo and
  demo link. The Submit button only appears inside that window.
- Demo video: 3 minutes or less. Must cover architecture, implementation, runtime,
  reasoning and result for each of neatlogs, Entire and cfo.ai.
- Public repo with commits dated inside the window, with supporting evidence in it.
- Judging: agent 30%, use of the three tools 25%, demo 20%, building in public 15%,
  usefulness and originality 10%.

| Claim judges check | Evidence we must produce |
|---|---|
| The agent improved | Before/after run pair with numbers compared |
| Used neatlogs | Trace links or screenshots |
| Used Entire | Checkpoints or entire-graph output from the repo |
| Used cfo.ai | Business plan: pricing, costs, revenue, runway |
| Recovers from failures | A run where an action failed, showing what happened next |
| Built in public | Links to posts tagged #neatHack |
| Code written in the window | Public repo commit dates |

## One Run

| Step | What happens | Focus area |
|---|---|---|
| 1. Plan | The model turns the Brief into a Run Plan: sources, areas, page budget, comp window, spend cap. It re-plans when a source is blocked or comps are too thin. In a Brief, Area is a hard limit, budget is hard plus 5% Headroom, and sizes and bedrooms are soft within about 20%. | Planning |
| 2. Collect | Tools fetch listing pages, starting from the Sheet's URLs. Every fetched page is saved as a Snapshot. Snapshots stay out of the public repo because full pages carry agents' names and phone numbers. | Tool use, Execution |
| 3. Extract | Structured data on the page (JSON-LD, meta tags) is read in code first. The model then reads the free text for what is missing and produces a Listing Record. Each field carries the source text it was read from. Only the relevant excerpt goes to the model. | Context |
| 4. Check | Deterministic Extraction Checks first. Then the Verifier, a separate agent on a different model, re-reads the Snapshot and judges the Record without seeing the Scout's reasoning. When they disagree, the Arbiter settles it: prefer structured data, re-fetch, or Quarantine. | Verification |
| 5. Recover | Failed fetch: back off and retry, then mark Unreachable. Failed check: the Scout re-extracts with the failure as feedback (twice at most), then Quarantine. Nothing is dropped silently. | Recovery |
| 6. Value | Deterministic. Comps are Confirmed Records in the same Area and of similar size to the Brief. Market Price is their median asking price per m2 for land and for building; the Valuation is the blended gap against it. | Core idea |
| 7. Rank and audit | Top candidates get a deeper second pass: re-fetch, duplicate search, wider comps. An Auditor recomputes each Dossier's numbers from stored evidence. Failures loop back to steps 3-4. | Iteration, Verification |
| 8. Report | Shortlist, a Dossier per listing, and a list of what was Quarantined and why. HTML and JSON. | |

State runs through all of it. Each step is checkpointed, so an interrupted Run resumes
without re-fetching. Across Runs the agent keeps price history per Listing and failure
rates per source, and the next Run Plan uses them.

Because Snapshots are saved, any Run can be replayed offline on the same inputs. That is
what makes the before/after pair a fair comparison, and it means the demo does not depend
on a portal being reachable.

## What each platform does

| Platform | Job in the workflow | Evidence it yields |
|---|---|---|
| neatlogs | Runtime: one trace per Run, spans per step, tool call and model call, with attributes for listing id, check name, outcome and retries. Detection rules on failed checks, retry counts, cost and latency. Build loop: read failing traces, fix, replay the same Snapshots, compare. | Trace links, before/after pair, recovery trace |
| Entire | Build time: Checkpoints link each commit to the Claude Code session that wrote it. entire-graph gives the coding agent a map of the repo as it grows. | Checkpoints, graph snapshot in `evidence/` |
| cfo.ai | The business plan: pricing, costs, revenue, runway. Inputs are measured: model cost per Run and per verified Listing from neatlogs, compute cost from AWS. A script writes `unit_economics.csv` from trace data and Ari imports it. Not used for property valuation. | Plan in `docs/business-plan/` |
| AWS credit | One EC2 instance (t3.small, us-east-1, Hackathon_VPC) serves the Dashboard at a public URL and fires each Job daily: cron calls `dealscout tick` every minute. Snapshots stay on its disk and are never served. | Live URL, real compute cost for the plan |
| Model | Any OpenAI-compatible endpoint, set in `.env`: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_FAST`, `LLM_MODEL_STRONG`. | |
| Crustdata | Not used. It is company and people data. | |

## Stack

Defaults I picked; all swappable.

- Python 3.12 with uv, pytest.
- LangGraph for the loop, with a SQLite checkpointer for state and resume.
- `langchain-openai` client pointed at the configurable base URL.
- neatlogs SDK, attached once per Run with `neatlogs.langchain_handler()`.
- Fetcher: plain HTTP, honours robots.txt, rate-limited, honest user agent. No bot-detection
  evasion. A blocked portal is a recovery case, not something to work around.
- Report: one generated static HTML file per Run, no build step. It stays on the instance.
- Dashboard: Python's own `http.server` behind nginx, pages rendered in code, Jobs and
  Listing lists in one SQLite file. No new dependency and no build step.

First-hour check: confirm tool calling works on the chosen model endpoint before building
on it.

## Repo layout

```
DealScout/
  AGENTS.md  CLAUDE.md      rules for every agent
  CONTEXT.md  PLAN.md  hackathon.md  README.md
  pyproject.toml  uv.lock  .env.example
  tasks/                    one brief per piece of work
  src/dealscout/
    domain/                 contracts: the types every lane exchanges
    collect/                fetcher, robots, Snapshot store
    extract/                structured-data readers per Portal, the Scout
    verify/                 Extraction Checks, Verifier, Arbiter
    value/                  Areas, Comps, Market Price, Valuation
    report/                 Shortlist and Dossier as HTML and JSON
    run/                    the loop, state, tracing, model client, CLI
    dashboard/              the Dashboard, the Job store, the daily tick
  tests/                    mirrors src; fixtures/ holds trimmed pages
  eval/                     answer key, scoring, before/after results
  data/urls/                corpus URL lists (snapshots/ and runs/ are ignored)
  deploy/                   EC2 setup: Dashboard service, nginx, cron tick
  docs/business-plan/       cfo.ai plan and unit_economics.csv
  evidence/                 trace links, screenshots, checkpoints, graph snapshot
  content/                  demo script, storyboard, posts, screenshots
```

## Several agents at once

Each agent works in a lane: a set of directories with exactly one writer, on its own branch
and worktree. `AGENTS.md` holds the rules; this section holds the reasoning.

| Lane | Writes to | Can start |
|---|---|---|
| integration (this session) | `domain/`, `run/`, `dashboard/`, dependencies, root docs, `tasks/`, all merges | Now |
| content | `content/` | Now: posts and demo storyboard need no code |
| collect | `collect/`, `extract/` | After contracts are merged |
| verify | `verify/`, `value/` | After contracts are merged |
| report | `report/`, `eval/` | After contracts are merged |
| ops | `deploy/`, `docs/business-plan/`, `evidence/` | Sunday afternoon |

- Contracts first. `domain/` is written and merged before any coder lane starts. Lanes code
  against the contracts and the fixtures, so they can run in parallel against fakes.
- One thin slice before fanning out. A single Listing goes end to end on `main` first, so
  the lanes fill in a shape that already runs.
- At most three coder lanes. Your review time is the bottleneck, not typing speed.
- The files every lane touches are handled once: only integration edits `pyproject.toml`
  and `uv.lock`, and `hackathon.md` uses a union merge so appended entries never conflict.
- Every coder must be an agent Entire can checkpoint (Claude Code, Codex, OpenCode, Cursor,
  Pi), enabled in the repo before it commits.
- To check in the first hour: that Entire records checkpoints from a worktree. If it does
  not, lanes take turns on `main` in separate sessions.

## Timeline (WIB)

| When | Work | Gate |
|---|---|---|
| Sat 16:20-17:00 | You: run setup commands, kickoff post. Me: read the Sheet, close round 2, write CONTEXT.md and hackathon.md | Decisions locked |
| Sat 17:00-18:00 | Repo, uv, Entire enabled, neatlogs hello-trace, tool-calling check, worktree checkpoint check | One trace and one checkpoint exist |
| Sat 18:00-20:30 | Integration lane only: contracts, then one Listing end to end on real pages. Content lane: kickoff post, storyboard | Thin slice runs on `main` |
| Sat 20:30-23:30 | Fan out: collect, verify and report lanes in parallel, merged back by 23:30 | Baseline Run traced (the "before") |
| Sat 23:30-00:00 | Post 2, hackathon.md entry, handoff note for the night | |
| Sat 00:00-07:00 | Unattended: answer key from Snapshots, scoring script, baseline numbers, test coverage | Baseline numbers |
| Sun 07:00-08:00 | You: review the night's work, spot-check 10 answer-key rows | |
| Sun 08:00-12:00 | Read failing traces in neatlogs, fix, replay, compare | Before/after pair |
| Sun 13:00-15:00 | Recovery paths, Detection rules | Recovery trace |
| Sun 15:00-17:00 | Rank-and-audit loop, resume after interruption | Iteration visible in a trace |
| Sun 17:00-19:00 | EC2 deploy | Public report URL |
| Sun 19:00-20:30 | cfo.ai plan from measured costs | Business plan in repo |
| Sun 20:30-23:00 | README, evidence folder, demo script. Feature freeze 23:00 | Repo submission-ready |
| Sun 23:00-06:30 | Unattended: fresh-clone test, docs, demo asset list | Reproducible from README |
| Mon 06:30-08:00 | Review, final Run for the demo | |
| Mon 08:00-13:00 | Record and edit the demo | Video at 3:00 or under |
| Mon 13:00-16:00 | Buffer, re-record, final commits | |
| Mon 16:00-20:00 | Evidence check against the table above, rest, draft the quote post | |
| Mon 20:30 | Submit on X | Hard close Tue 01:25 |

## Cut order if behind

1. Memory across Runs.
2. EC2 deploy (the Dashboard then runs on the builder's machine for the demo).
3. Discovery from portal search pages (use Sheet URLs as the only source of listings).
4. Report styling.

Never cut: the before/after pair, the recovery trace, the cfo.ai plan, Entire checkpoints,
the demo.

## Decisions

- Corpus: the Sheet's listing URLs from the last 14 days, on the five portals that answered
  the fetch test. OLX rows stay in, so the agent has to mark them Unreachable.
- Areas: the seven with enough samples in the Sheet: BSD/Serpong, Gading Serpong, Bintaro,
  Depok, Yogyakarta, Sleman, Bantul.
- Valuation: three tiers (Below, At, Above Market), with Split when land and building disagree.
  Expected price is the mean of two estimates: land size times the Area's median price per
  m2 of land, and building size times its median per m2 of building. Ratio = asking price /
  expected price. Below Market under 0.90, Above Market over 1.10, At Market between. The
  land ratio and building ratio are tiered the same way; Split is set when they land in
  different tiers.
- Brief limits: Area hard; budget hard plus 5% Headroom, raisable to 10%; sizes and
  bedrooms soft within about 20%.
- Model: any OpenAI-compatible endpoint for local testing; a pay-as-you-go key for recorded
  and deployed Runs.
- EC2: yes. It serves the Dashboard and fires Jobs. The Dashboard is how a buyer uses
  DealScout, so the deploy is no longer first on the cut list.
- Jobs: a Job's Listing URLs are the corpus URLs on its Portals. Portal search pages are
  not crawled. A Brief change makes a new Job; the old one keeps its list and stops firing.
- Before/after metric: about 40 Snapshots with a confirmed answer key, scored on field
  accuracy, true Deals in the top 10, cost per Run and time per Run. The builder spot-checks
  10 answer-key rows.
- Unattended work overnight: commit, push, run tests and local Runs under a spend cap. No
  AWS changes, no posts, nothing installed outside the project.
- Published name: Riftar. Posts are drafted by an agent and published by the builder.
- Fetching: plain requests that honour robots.txt and crawl delays. No bot-protection bypass.
