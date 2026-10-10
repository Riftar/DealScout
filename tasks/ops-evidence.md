# Ops and evidence

Lane: ops. Branch: `lane/ops`. Writes `deploy/`, `docs/business-plan/`, `evidence/`.
Starts after the first traced Run is on `main`.

## Build

1. `evidence/`:
   - the before/after Run pair with numbers;
   - neatlogs trace ids and screenshots;
   - the trace of a Run where a fetch failed and the Run recovered;
   - `entire checkpoint list` output and one Entire checkpoint link,
     `https://entire.io/gh/Riftar/DealScout/commit/<sha>`;
   - `entire graph stats --repo .` and one `entire graph diff` between two commits.
2. `docs/business-plan/unit_economics.csv`: cost per Run measured from neatlogs traces, for
   the builder to hand to cfo.ai. The builder exports the cfo.ai plan (pricing, costs,
   revenue, runway) into `docs/business-plan/`.
3. `deploy/`: a script and notes for one EC2 instance (us-east-1, the supplied
   Hackathon_VPC, t3.small) that runs a scheduled Run and serves the report. The builder
   launches it; AWS changes are the builder's.

## Done

- Every file in `evidence/` is free of keys, phone numbers and people's names.
- Each row of `PLAN.md` "Hard requirements" has a file in `evidence/`.

## Requests

(none yet)
