# Collect and extract

Lane: collect. Branch: `lane/collect`. Writes `src/dealscout/collect/`,
`src/dealscout/extract/`, `tests/collect/`, `tests/extract/`.

## Build

1. `extract/text.py`: `read_text(record, model) -> ListingRecord`. The Scout's model reads
   `record.description` and fills only the required fields that are still missing (see
   `ListingRecord.missing_required()`). Each filled field gets `sources[field] = MODEL` and
   `evidence[field]` = the exact words from the advert. A value the advert does not state
   stays `None`.
2. `read_text` also records in `evidence` what the advert text states for fields the
   structured data already filled, so the verify lane can compare the two. Real case: a
   99.co page whose data says building 60 m2 while its text says 62 m2.
3. Structured readers for pinhome, masuksini and idrumah in `extract/structured.py`, in the
   style of the two that exist. Fetch one real page of each through `Fetcher` to learn its
   shape.
4. `collect/corpus.py`: build `data/urls/corpus.txt` from the builder's tracker export in
   `data/raw/` (ignored by git): Listings from the last 14 days on the five readable
   Portals plus the OLX rows, de-duplicated by URL.
5. Duplicates: the same house advertised twice gets `duplicate_of` set to the first URL.

Tests use hand-written pages and a fake model. Real pages stay in `data/snapshots/`.

## Done

- `uv run pytest tests/collect tests/extract` passes.
- A table in `hackathon.md`: for each Portal, pages fetched, and how many of the eight
  required fields the structured reader filled on average.

## Requests

(none yet)
