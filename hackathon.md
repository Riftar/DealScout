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

Open at the end of the session:

- Entire CLI 0.11.4 is installed but not logged in or enabled in this repo.
- The neatlogs CLI is not installed and no trace has been sent.
- Whether Entire records Checkpoints from a git worktree is untested.
- No portal has been tested from an AWS address. Lamudi and jualrumahjakarta are untested.

Planned next:

- Setup gate: Entire enabled, a first Checkpoint, a neatlogs hello-trace, a tool-calling
  check on the chosen model endpoint.
- Contracts in `src/dealscout/domain/`, then one Listing end to end.

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
