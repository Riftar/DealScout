#!/usr/bin/env bash
# Renders each poster page to a 1600x900 PNG with headless Edge.
# Usage: bash content/posters/render.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd -W 2>/dev/null || pwd)"
edge="${EDGE:-/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"

for name in what-it-does two-sizes ninety-in-a-hundred; do
  "$edge" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=1600,900 --virtual-time-budget=10000 \
    --screenshot="$here/$name-1600x900.png" "file:///$here/$name.html" >/dev/null 2>&1
  echo "$name-1600x900.png"
done
