#!/usr/bin/env bash
# Queue the Jobs whose daily time has come and carry out one queued Run. Cron calls this
# every minute; a tick with nothing to do exits at once, and Runs never overlap.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PATH="$HOME/.local/bin:$PATH"
exec uv run dealscout tick
