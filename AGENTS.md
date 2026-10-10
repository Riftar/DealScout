# Working in DealScout

Several agents build this repo at once. Each works in a **lane**: a set of directories with
exactly one writer.

## Before you write

1. Read `CONTEXT.md` and use its terms exactly, in code, tests, commits and prose.
2. Read `tasks/README.md` for the current state, then your task brief under `tasks/`. It
   names your lane and what done looks like.
3. Work on your lane's branch, `lane/<name>`, in its own worktree.

## Lanes

| Lane | Writes to |
|---|---|
| integration | `src/dealscout/domain/`, `src/dealscout/run/`, `pyproject.toml`, `uv.lock`, root docs, `tasks/` |
| collect | `src/dealscout/collect/`, `src/dealscout/extract/`, and their tests |
| verify | `src/dealscout/verify/`, `src/dealscout/value/`, and their tests |
| report | `src/dealscout/report/`, `eval/`, and their tests |
| ops | `deploy/`, `docs/business-plan/`, `evidence/` |
| content | `content/` |

Write inside your lane; read anywhere. When you need a change outside your lane, add it to
the "Requests" section of your task brief and carry on against a fake.

## Contracts

`src/dealscout/domain/` holds the **contracts**: the types every lane exchanges. Contracts
and the pages in `tests/fixtures/` are the whole surface between lanes. The integration lane
is the only one that changes a contract.

## Done

A piece of work is done when:

- your lane's tests pass with `uv run pytest tests/<your package>`,
- it is committed on your lane branch,
- `hackathon.md` has your dated entry: what changed, which tests ran, what still fails.

The integration lane merges lanes into `main`.

Commit with `ENTIRE_TEST_TTY=0` set. Entire's commit hook otherwise waits for a terminal
answer that an agent cannot give, and the commit hangs.

## Hackathon rules that bind every lane

- Every line here is written in this repo, during the hackathon. Third-party code arrives as
  a dependency, added by the integration lane.
- Requests to a Portal go through the fetcher in `collect/`, which honours robots.txt and
  crawl delays.
- Session transcripts are pushed to this public repo by Entire. Keep keys, passwords and
  personal details out of the chat.
- Snapshots, Run output and `.env` stay local. Files in `evidence/` and `content/` are
  checked free of API keys, phone numbers and people's names before they are committed.
- A number in a post, the README or the demo comes from `evidence/` or `hackathon.md`.
  Measure it first if it is missing.

## Where things are explained

- `CONTEXT.md`: the glossary.
- `PLAN.md`: what DealScout does, the timeline, the evidence the judges check.
- `hackathon.md`: the build log.

<!-- entire-graph:begin -->
This repo has the entire-graph code graph installed. Before exploring code with
grep/find/whole-file reads, read .entire/graph-agent.md — resolution-first guidance
for using graph retrieval, focused source inspection, and verification.
@.entire/graph-agent.md
<!-- entire-graph:end -->
