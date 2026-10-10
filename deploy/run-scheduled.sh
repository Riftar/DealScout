#!/usr/bin/env bash
# Run one Brief end to end and write report under data/runs/. Intended for cron on EC2.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export ENTIRE_TEST_TTY=0
uv run dealscout run \
  --area Bintaro \
  --budget 1500000000 \
  --urls data/urls/seed.txt
