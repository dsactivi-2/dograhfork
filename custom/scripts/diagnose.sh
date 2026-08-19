#!/usr/bin/env bash
# Print enough to see why Dograh + Guardian is unhappy. Never prints secret values.
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yaml:custom/compose.overlay.yaml}"

ok() { printf '  OK   %s\n' "$1"; }
bad() { printf '  FAIL %s\n' "$1"; }
info() { printf '  --   %s\n' "$1"; }

echo "=== VoiceEU diagnose ==="
echo "cwd     $ROOT"
echo "branch  $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
echo "head    $(git rev-parse --short HEAD 2>/dev/null || echo '?')"
echo "compose $COMPOSE_FILE"
echo

echo "--- overlay ---"
if [[ -f custom/providers/deepgram_eu/config.py ]]; then
  ok "custom/providers/deepgram_eu/config.py"
else
  bad "Deepgram EU missing — checkout Guardian-Dograh"
fi
if [[ -f custom/compose.overlay.yaml ]]; then
  ok "custom/compose.overlay.yaml"
else
  bad "compose overlay missing"
fi

echo
echo "--- healthcheck ---"
if command -v python3 >/dev/null 2>&1; then
  python3 custom/guardian/healthcheck.py
  hc=$?
  case "$hc" in
    0) ok "healthcheck exit 0" ;;
    2) bad "healthcheck 2 — custom/ incomplete" ;;
    3) bad "healthcheck 3 — CUSTOM-SEAM lost" ;;
    4) bad "healthcheck 4 — forbidden US Deepgram edit" ;;
    *) bad "healthcheck exit $hc" ;;
  esac
else
  bad "python3 not installed (needed for healthcheck)"
fi

echo
echo "--- .env (keys only) ---"
if [[ -f .env ]]; then
  for key in OSS_JWT_SECRET POSTGRES_PASSWORD PUBLIC_HOST PUBLIC_BASE_URL TURN_HOST ENABLE_COTURN GUARDIAN_TOKEN GUARDIAN_PORT; do
    if grep -q "^${key}=" .env; then
      val="$(grep "^${key}=" .env | head -1 | cut -d= -f2-)"
      if [[ -z "$val" ]]; then
        bad "$key is empty"
      elif [[ "$key" == "PUBLIC_HOST" || "$key" == "PUBLIC_BASE_URL" || "$key" == "TURN_HOST" || "$key" == "ENABLE_COTURN" || "$key" == "GUARDIAN_PORT" ]]; then
        ok "$key=$val"
      else
        ok "$key is set (${#val} chars)"
      fi
    else
      info "$key not in .env"
    fi
  done
else
  bad ".env missing — run sudo ./setup_remote.sh (VPS) or deploy.sh (laptop)"
fi

echo
echo "--- docker ---"
if ! command -v docker >/dev/null 2>&1; then
  bad "docker not installed"
else
  ok "docker $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo present)"
  if docker compose version >/dev/null 2>&1; then
    ok "$(docker compose version | head -1)"
  else
    bad "docker compose plugin missing"
  fi
fi

if [[ -f docker-compose.yaml ]] && command -v docker >/dev/null 2>&1; then
  echo
  echo "--- containers ---"
  docker compose ps || true
  echo
  echo "--- api image ---"
  img="$(docker compose images api --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | head -1 || true)"
  if [[ -z "$img" ]]; then
    info "api image not built/started yet"
  elif [[ "$img" == *dograh-guardian-api* ]]; then
    ok "api image $img (overlay build)"
  else
    bad "api image $img — stock image, Deepgram EU will be missing. Use deploy.sh"
  fi
fi

echo
echo "--- endpoints ---"
probe() {
  local name=$1 url=$2
  if out="$(curl -skS -m 4 -o /tmp/dograh-diag.body -w '%{http_code}' "$url" 2>/tmp/dograh-diag.err)"; then
    if [[ "$out" == 2* || "$out" == 3* ]]; then
      ok "$name $url → $out"
    else
      bad "$name $url → HTTP $out"
    fi
  else
    bad "$name $url → $(tr '\n' ' ' </tmp/dograh-diag.err)"
  fi
}
probe "dograh api" "http://127.0.0.1:8000/api/v1/health"
probe "guardian" "http://127.0.0.1:8787/api/health"
probe "dograh ui" "http://127.0.0.1:3010/"

echo
echo "--- ports on this host ---"
if command -v ss >/dev/null 2>&1; then
  ss -lptn 2>/dev/null | grep -E ':80|:443|:3010|:8000|:8787' || info "none of 80/443/3010/8000/8787 listening"
else
  info "ss not available"
fi

echo
echo "--- disk / memory ---"
df -h . | tail -1
if command -v free >/dev/null 2>&1; then
  free -h | head -2
fi

echo
echo "Fertig. Fehlerbehebung: custom/DEPLOY.md  (Abschnitt Fehlerbehebung)"
