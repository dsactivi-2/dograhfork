#!/usr/bin/env bash
# Safe upstream merge for the VoiceEU custom branch.
# Never run this on a dirty tree. Stops if healthcheck fails after merge.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "dirty tree — commit or stash first" >&2
  exit 1
fi

git checkout custom
BACKUP="custom/backup-$(date +%Y%m%d-%H%M)"
git branch "$BACKUP"
echo "backup branch: $BACKUP"

git fetch upstream --tags
git checkout main
git merge --ff-only upstream/main
git checkout custom
git merge --no-ff upstream/main -m "merge(upstream): $(date +%Y-%m-%d)"

git submodule update --init --recursive
python3 custom/guardian/apply_branding.py
python3 custom/guardian/healthcheck.py
echo "merge + branding + healthcheck OK. Push: git push origin custom"
