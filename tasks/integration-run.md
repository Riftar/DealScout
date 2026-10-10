# Integration: the Run

Lane: integration. Branch: `main` (this lane owns it).

## Build

1. `src/dealscout/run/llm.py`: `scout_model()` from `LLM_MODEL_FAST` and `verifier_model()`
   from `LLM_MODEL_STRONG`, both `ChatOpenAI` on `LLM_BASE_URL`. `run/smoke.py` shows the
   working call.
2. `src/dealscout/run/graph.py`: one Run as a LangGraph graph with a SQLite checkpointer in
   `data/state/`, so a stopped Run resumes. Steps, as in `PLAN.md` "One Run": Plan, Collect,
   Extract, Check, Recover, Value, Rank and audit, Report.
3. Recover: a Listing whose fetch or read failed gets one retry, then is marked Unreachable
   or Quarantined with the reason. The Run always finishes.
4. `src/dealscout/run/cli.py`: `dealscout run --area Bintaro --budget 1500000000
   --urls data/urls/seed.txt`. Prints the Shortlist and the report path.
5. neatlogs: `neatlogs.init(workflow_name="dealscout-run")`, one `neatlogs.trace` per Run,
   the LangChain handler passed once at `graph.invoke(..., config={"callbacks": [handler]})`,
   `neatlogs.flush()` at the end.

Call the other lanes through the seams in `tasks/README.md`. Until a lane merges, keep a
fake for it under `src/dealscout/run/fakes.py`.

## Done

- `uv run pytest tests/run` passes, with the graph tested end to end on fakes.
- `uv run dealscout run ...` over `data/urls/seed.txt` finishes and its trace is visible
  with `neatlogs.cmd --project <id> traces list --workflow dealscout-run`.
- The trace id, token count and wall time are in `hackathon.md`.

## Requests

(none yet)
