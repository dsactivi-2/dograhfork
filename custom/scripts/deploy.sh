#!/usr/bin/env bash
# One command: start Dograh + VoiceEU overlay + Guardian.
#   ./custom/scripts/deploy.sh           # local (ports 3010 + 8787)
#   ./custom/scripts/deploy.sh remote    # VPS after sudo ./setup_remote.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yaml:custom/compose.overlay.yaml}"
MODE="${1:-local}"

if [[ ! -f docker-compose.yaml ]]; then
  echo "docker-compose.yaml missing — run this from the dograhfork checkout." >&2
  exit 2
fi

if [[ ! -d custom/providers/deepgram_eu ]]; then
  echo "custom/ overlay missing. Checkout branch Guardian-Dograh." >&2
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required." >&2
  exit 2
fi

python3 custom/guardian/healthcheck.py || {
  echo "Guardian healthcheck failed before start. Fix seams first." >&2
  exit 3
}

if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream https://github.com/dograh-hq/dograh.git || true
fi

generate_secret() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import secrets; print(secrets.token_hex(32))'
    return
  fi
  openssl rand -hex 32
}

ensure_env_key() {
  local key=$1
  if [[ -f .env ]] && grep -q "^${key}=" .env; then
    return
  fi
  printf '%s=%s\n' "$key" "$(generate_secret)" >> .env
  echo "wrote $key to .env"
}

if [[ ! -f .env ]]; then
  : > .env
fi
ensure_env_key OSS_JWT_SECRET
ensure_env_key POSTGRES_PASSWORD
ensure_env_key REDIS_PASSWORD
ensure_env_key MINIO_ROOT_USER
ensure_env_key MINIO_ROOT_PASSWORD

if [[ "$MODE" == "remote" ]]; then
  if ! grep -q '^PUBLIC_HOST=.\+' .env 2>/dev/null; then
    echo "Remote deploy needs PUBLIC_HOST in .env. Run: sudo ./setup_remote.sh" >&2
    exit 2
  fi
  echo "Starting remote stack (Dograh + Guardian)…"
  exec ./remote_up.sh --build
fi

if [[ "$MODE" != "local" ]]; then
  echo "usage: $0 [local|remote]" >&2
  exit 2
fi

echo "Starting local stack (Dograh :3010 + Guardian :8787)…"
docker compose --profile tunnel up -d --build

echo
echo "Dograh UI     http://localhost:3010"
echo "Guardian      http://localhost:8787"
echo "Dograh API    http://localhost:8000/api/v1/health"
echo
echo "In Dograh pick STT/TTS: Deepgram US  or  Deepgram EU  (both must appear)."
echo "Updates later:  custom/guardian/update.sh"
