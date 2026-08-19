#!/usr/bin/env bash
# Safe upstream merge for Guardian-Dograh (or the current overlay branch).
# Never run this on a dirty tree. Stops if healthcheck fails after merge.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "Guardian-Dograh" && "$BRANCH" != "custom" ]]; then
  echo "refusing to merge on '$BRANCH' — checkout Guardian-Dograh first" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "dirty tree — commit or stash first" >&2
  exit 1
fi

if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream https://github.com/dograh-hq/dograh.git
fi

BACKUP="${BRANCH}-backup-$(date +%Y%m%d-%H%M)"
git branch "$BACKUP"
echo "backup branch: $BACKUP"

git fetch upstream --tags
git merge --no-ff upstream/main -m "merge(upstream): $(date +%Y-%m-%d)"

git submodule update --init --recursive
python3 custom/guardian/apply_branding.py
python3 custom/guardian/healthcheck.py
echo "merge + branding + healthcheck OK."
echo "Redeploy: ./custom/scripts/deploy.sh remote"
echo "Push:     git push origin $BRANCH"
