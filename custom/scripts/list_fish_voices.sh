#!/usr/bin/env bash
# List Fish Audio voice IDs (reference_id) for the current API key.
# Usage: FISH_API_KEY=... bash custom/scripts/list_fish_voices.sh
set -euo pipefail

KEY="${FISH_API_KEY:-}"
if [[ -z "$KEY" ]]; then
  echo "Set FISH_API_KEY first (only for this script, not for Dograh)." >&2
  exit 2
fi

# self=true → own workspace. Drop it to search the public library (add title=...).
QS="page_size=50&page_number=1&self=true"
if [[ -n "${1:-}" ]]; then
  QS="page_size=50&page_number=1&title=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))' "$1")"
fi

BODY="$(curl -fsS "https://api.fish.audio/model?${QS}" \
  -H "Authorization: Bearer ${KEY}")"

python3 - "$BODY" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
items = data.get("items") or []
if not items:
    print("No voices. Clone one in the Fish dashboard or search: list_fish_voices.sh <title>")
    sys.exit(0)
print(f"{'voice (→ Dograh TTS field)':<40} title")
for item in items:
    vid = item.get("_id") or item.get("id") or ""
    title = item.get("title") or ""
    print(f"{vid:<40} {title}")
print(f"\n{data.get('total', len(items))} total — paste the left column into TTS voice")
PY
