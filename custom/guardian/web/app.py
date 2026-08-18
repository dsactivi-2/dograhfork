#!/usr/bin/env python3
"""Guardian sidecar. Talks to Dograh over the compose network. Stdlib only."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "0.0.0.0"
PORT = int(os.environ.get("GUARDIAN_PORT", "8787"))
DOGRAH_API = os.environ.get("DOGRAH_API_URL", "http://api:8000").rstrip("/")
DOGRAH_UI = os.environ.get("DOGRAH_UI_URL", "http://ui:3010").rstrip("/")
TOKEN = os.environ.get("GUARDIAN_TOKEN", "").strip()
REPO_ROOT = Path(os.environ.get("REPO_ROOT", "/probe"))
OVERLAY = Path(os.environ.get("OVERLAY_ROOT", str(REPO_ROOT / "custom")))
STATIC = Path(__file__).resolve().parent / "static"
STARTED = time.time()

PROVIDERS = [
    {
        "id": "deepgram",
        "name": "Deepgram US",
        "kind": "stt/tts",
        "origin": "upstream",
        "base_url": "https://api.deepgram.com",
    },
    {
        "id": "deepgram_eu",
        "name": "Deepgram EU",
        "kind": "stt/tts",
        "origin": "overlay",
        "base_url": "https://api.eu.deepgram.com",
    },
    {
        "id": "fish_audio",
        "name": "Fish Audio",
        "kind": "tts",
        "origin": "overlay",
        "base_url": "https://api.fish.audio",
    },
    {
        "id": "telnyx",
        "name": "Telnyx",
        "kind": "telephony",
        "origin": "upstream",
        "base_url": None,
    },
]


def probe(url: str, timeout: float = 4.0) -> dict:
    started = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dograh-guardian/0.2"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = res.read(4000).decode("utf-8", "replace")
            return {
                "ok": 200 <= res.status < 400,
                "status": res.status,
                "ms": int((time.time() - started) * 1000),
                "body": body[:400],
            }
    except Exception as exc:  # noqa: BLE001 — sidecar must never crash a probe
        return {
            "ok": False,
            "status": 0,
            "ms": int((time.time() - started) * 1000),
            "body": f"{exc.__class__.__name__}: {exc}",
        }


def overlay_files() -> list[dict]:
    rows = []
    if not OVERLAY.is_dir():
        return rows
    for path in sorted(OVERLAY.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        rel = str(path.relative_to(OVERLAY.parent))
        rows.append({"path": rel, "bytes": path.stat().st_size})
    return rows


def run_healthcheck() -> dict:
    script = OVERLAY / "guardian" / "healthcheck.py"
    if not script.is_file():
        return {"ok": False, "code": 2, "output": "healthcheck.py missing"}
    env = os.environ.copy()
    try:
        proc = subprocess.run(
            ["python3", str(script)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=env,
        )
    except OSError:
        proc = subprocess.run(
            ["python", str(script)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=env,
        )
    output = (proc.stdout or "") + (proc.stderr or "")
    return {"ok": proc.returncode == 0, "code": proc.returncode, "output": output.strip()}


def snapshot() -> dict:
    api = probe(f"{DOGRAH_API}/api/v1/health")
    ui = probe(DOGRAH_UI)
    check = run_healthcheck()
    files = overlay_files()
    eu = (OVERLAY / "providers" / "deepgram_eu" / "config.py").is_file()
    us_file = (
        REPO_ROOT
        / "api"
        / "services"
        / "configuration"
        / "options"
        / "deepgram.py"
    )
    us_text = us_file.read_text(encoding="utf-8", errors="replace") if us_file.is_file() else ""
    us_untouched = "api.eu.deepgram.com" not in us_text and "CUSTOM-SEAM" not in us_text
    return {
        "product": "dograh-guardian",
        "version": "0.2.0",
        "uptime_s": int(time.time() - STARTED),
        "dograh": {"api": api, "ui": ui},
        "overlay": {
            "present": OVERLAY.is_dir(),
            "deepgram_eu": eu,
            "file_count": len(files),
        },
        "healthcheck": check,
        "providers": PROVIDERS,
        "wired": bool(api["ok"] and eu),
        "us_provider_intact": us_untouched,
        "links": {
            "dograh_ui": DOGRAH_UI,
            "dograh_api": f"{DOGRAH_API}/api/v1/health",
            "guardian": f"http://0.0.0.0:{PORT}",
        },
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "Guardian/0.2"

    def log_message(self, fmt: str, *args) -> None:
        print(f"guardian {self.address_string()} {fmt % args}")

    def _authed(self) -> bool:
        if not TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        if header == f"Bearer {TOKEN}":
            return True
        cookie = self.headers.get("Cookie", "")
        return f"guardian_token={TOKEN}" in cookie

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: object) -> None:
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/api/health", "/health"):
            self._json(200, {"ok": True, "service": "guardian"})
            return
        if not self._authed():
            self._json(401, {"ok": False, "error": "set GUARDIAN_TOKEN and send Bearer"})
            return
        if path in ("/", "/index.html"):
            html = (STATIC / "index.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return
        if path == "/api/status":
            self._json(200, snapshot())
            return
        if path == "/api/checks":
            self._json(200, run_healthcheck())
            return
        if path == "/api/overlay":
            self._json(200, {"files": overlay_files()})
            return
        if path == "/api/providers":
            self._json(200, {"providers": PROVIDERS})
            return
        if path.startswith("/static/"):
            target = (STATIC / path[len("/static/") :]).resolve()
            if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
                self._json(404, {"error": "not found"})
                return
            ctype = "text/css" if target.suffix == ".css" else "application/octet-stream"
            self._send(200, target.read_bytes(), ctype)
            return
        self._json(404, {"error": "not found"})


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"guardian listening on {HOST}:{PORT} api={DOGRAH_API}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
