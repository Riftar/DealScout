# DealScout

Tell it the house you want. It tells you what that house should cost in that area, and which
listings beat that price, with proof from each listing's own page.

Built solo for [neatHack](https://neatlogs.com/hackathon), 10 to 12 October 2026.

## Status

The project scaffold and the contracts in `src/dealscout/domain/` exist; no Listing has
been read yet. This section is updated as the build goes on;
`hackathon.md` has the dated log.

## Why

A tracker of about 4,990 Indonesian house listings, collected automatically over four
months, is the starting point. In 100 rows sampled from the later part of it, only 10 had
both a land size and a building size, so the rest could not be priced at all. Other sampled
rows held bathroom counts of 89 and 205, and a 178 m² house recorded at Rp 165 Juta.

In a deal screen, the listing that looks cheapest is often the one that was misread.
DealScout checks its own reading of every listing against the source page, and spends the
most effort on the listings that look best.

## How it works

Three agents share one Run:

- the **Scout** collects listings and records what each one says,
- the **Verifier** re-reads each saved page on a different model, without seeing the
  Scout's reasoning,
- the **Arbiter** settles any disagreement, or sets the listing aside with the reason.

Only confirmed listings are priced against comparable houses or ranked.

## Read more

- [PLAN.md](PLAN.md): the workflow, the timeline and the evidence the judges check.
- [CONTEXT.md](CONTEXT.md): the glossary.
- [AGENTS.md](AGENTS.md): how several coding agents work in this repo at once.
- [hackathon.md](hackathon.md): the build log.

## Data and fetching

Listing pages are fetched with plain requests that honour each portal's robots.txt and
crawl delay. Saved pages stay off this repo because they carry people's names and phone
numbers.
