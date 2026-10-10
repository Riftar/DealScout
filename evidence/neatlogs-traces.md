# neatlogs traces

Workflow names in code: `dealscout-smoke` (`run/smoke.py`), `dealscout-run` (`run/cli.py`).

| When | Workflow | Trace id | Notes |
|---|---|---|---|
| Setup check, 10 Oct ~17:00 WIB | `dealscout-smoke` | `99136eadf37cbd8e9c3c77da929fc23d` | Both models returned expected tool call; flush OK; 5,549 tokens (hackathon.md) |
| First live Run, 10 Oct ~17:40 WIB | `dealscout-run` | `1d5e860da95bc00cac30b0b554a9860a` | 12 URLs, Bintaro, budget Rp 1.5e9; 39.3 s wall; 2,649 tokens; confirmed=8, quarantined=4, unreachable=0, deals=0 |

Open each trace in the neatlogs project UI and save screenshots under `neatlogs/`
before submission (builder step; PNGs stay out of git until checked for contact details).

Recovery trace on neatlogs: pending a live Run that fails a fetch and completes
Recover (see `recovery.md`). The graph and tests already implement the path.
