# Verify and value

Lane: verify. Branch: `lane/verify`. Writes `src/dealscout/verify/`,
`src/dealscout/value/`, `tests/verify/`, `tests/value/`.

## Build

1. `verify/checks.py`: `run_checks(record) -> list[CheckFailure]`, in code, no model.
   Each failure seen in the builder's old data is a check:
   - a required field is missing;
   - bedrooms or bathrooms above 20;
   - land or building size outside 15 to 5,000 m2;
   - price outside Rp 100 million to Rp 100 billion;
   - a price in the URL or title that differs from the recorded price by more than 15%;
   - property type that is not a house;
   - a structured value that differs from the advert text's value in `record.evidence`.
2. `verify/verifier.py`: `verify(record, html, model) -> list[Disagreement]`. The Verifier
   reads the Snapshot on the strong model and never sees the Scout's values or reasoning.
   Its answers are compared with the record in code.
3. `verify/arbiter.py`: `arbitrate(record, disagreements, html, model) -> ListingRecord`.
   For each Disagreement the Arbiter is shown both values and must quote the page. It
   settles the field, or the record becomes Quarantined with the reason. A record with no
   failures and no open Disagreement becomes Confirmed.
4. `value/market.py`: `market_price(area, confirmed)`. Comps are Confirmed records in the
   same Area; the Market Price is the median asking price per m2 of land and of building.
   Fewer than three Comps returns `None`.
5. `value/valuation.py`: `value(record, market)` and `shortlist(brief, confirmed)`. The
   formula, tiers and Split rule are in `PLAN.md` "Decisions", under Valuation. A Deal is Confirmed, inside the Brief's
   hard limits (Area, `Brief.price_ceiling_rp`), and Below Market. Soft misses on size and
   bedrooms are listed on the Deal and never drop it.

Tests use hand-built records and a fake model.

## Done

- `uv run pytest tests/verify tests/value` passes.
- Each check in step 1 has a test with a record that trips it and one that passes.

## Requests

(none yet)
