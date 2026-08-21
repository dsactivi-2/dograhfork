#!/bin/sh
set -eu
mkdir -p "${STATE_DIR:-/state}/snapshots"
chmod -R a+rwx "${STATE_DIR:-/state}" 2>/dev/null || true
exec python -u /srv/app.py
