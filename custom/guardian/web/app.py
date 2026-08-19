#!/usr/bin/env python3
"""Guardian sidecar: config, history, MCP. Stdlib only."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from inventory import build_inventory
from mcp import TOOLS, discovery, handle_rpc
from store import (
    OVERLAY,
    REPO,
    agent_combo,
    list_history,
    load_config,
    record_boot_snapshot,
    redact,
    save_config,
    write_runtime_env,
)

HOST = "0.0.0.0"
PORT = int(os.environ.get("GUARDIAN_PORT", "8787"))
DOGRAH_API = os.environ.get("DOGRAH_API_URL", "http://api:8000").rstrip("/")
DOGRAH_UI = os.environ.get("DOGRAH_UI_URL", "http://ui:3010").rstrip("/")
TOKEN = os.environ.get("GUARDIAN_TOKEN", "").strip()
STATIC = Path(__file__).resolve().parent / "static"
STARTED = time.time()

PROVIDERS = [
    {
        "id": "deepgram",
        "name": "Deepgram US",
        "kind": "stt/tts",
        "origin": "upstream",
        "base_url": "https://api.deepgram.com",
        "ui": True,
        "factory": "official defaults, no DEEPGRAM_BASE_URL",
    },
    {
        "id": "deepgram_eu",
        "name": "Deepgram EU",
        "kind": "stt/tts",
        "origin": "overlay",
        "base_url": "https://api.eu.deepgram.com",
        "ui": True,
        "factory": "fixed EU host",
    },
    {
        "id": "deepgram_2",
        "name": "Deepgram 2",
        "kind": "stt",
        "origin": "overlay",
        "base_url": "DEEPGRAM_BASE_URL (default EU)",
        "ui": True,
        "factory": "interim + smart_format + punctuate",
    },
    {
        "id": "deepgram_3",
        "name": "Deepgram 3",
        "kind": "stt",
        "origin": "overlay",
        "base_url": "DEEPGRAM_BASE_URL (default EU)",
        "ui": True,
        "factory": "endpointing 400, numerals, vad_events, interim off",
    },
    {
        "id": "fish_audio",
        "name": "Fish Audio",
        "kind": "tts",
        "origin": "overlay",
        "base_url": "https://api.fish.audio",
        "ui": True,
        "factory": "voice required, pcm, pipeline sample_rate",
    },
    {
        "id": "telnyx",
        "name": "Telnyx",
        "kind": "telephony",
        "origin": "upstream",
        "base_url": None,
        "ui": True,
        "factory": "official — do not fork",
    },
]


def probe(url: str, timeout: float = 4.0) -> dict:
    started = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dograh-guardian/0.3"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = res.read(4000).decode("utf-8", "replace")
            return {
                "ok": 200 <= res.status < 400,
                "status": res.status,
                "ms": int((time.time() - started) * 1000),
                "body": body[:400],
            }
    except Exception as exc:  # noqa: BLE001
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
        if any(
            part.startswith(".") or part in {"__pycache__", "state"}
            for part in path.parts
        ):
            continue
        rel = str(path.relative_to(OVERLAY.parent))
        rows.append({"path": rel, "bytes": path.stat().st_size})
    return rows


def run_healthcheck() -> dict:
    script = OVERLAY / "guardian" / "healthcheck.py"
    if not script.is_file():
        return {"ok": False, "code": 2, "output": "healthcheck.py missing"}
    env = os.environ.copy()
    for bin_name in ("python3", "python"):
        try:
            proc = subprocess.run(
                [bin_name, str(script)],
                cwd=str(REPO),
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env=env,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
            return {
                "ok": proc.returncode == 0,
                "code": proc.returncode,
                "output": output.strip(),
            }
        except FileNotFoundError:
            continue
    return {"ok": False, "code": 2, "output": "python not found"}


def snapshot() -> dict:
    api = probe(f"{DOGRAH_API}/api/v1/health")
    ui = probe(DOGRAH_UI)
    check = run_healthcheck()
    files = overlay_files()
    eu = (OVERLAY / "providers" / "deepgram_eu" / "config.py").is_file()
    us_file = REPO / "api" / "services" / "configuration" / "options" / "deepgram.py"
    us_text = (
        us_file.read_text(encoding="utf-8", errors="replace")
        if us_file.is_file()
        else ""
    )
    us_untouched = "api.eu.deepgram.com" not in us_text and "CUSTOM-SEAM" not in us_text
    cfg = load_config()
    return {
        "product": "dograh-guardian",
        "version": "0.4.0",
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
        "config": redact(cfg),
        "combo": redact(agent_combo(cfg)),
        "mcp": {
            "path": "/mcp",
            "tools": [t["name"] for t in TOOLS],
        },
        "links": {
            "dograh_ui": DOGRAH_UI,
            "dograh_api": f"{DOGRAH_API}/api/v1/health",
            "guardian": f"http://0.0.0.0:{PORT}",
        },
    }


def _contract() -> dict:
    path = OVERLAY / "contract" / "overlay.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"error": "missing contract"}


class Handler(BaseHTTPRequestHandler):
    server_version = "Guardian/0.3"

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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: object) -> None:
        self._send(
            code,
            json.dumps(payload, indent=2).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}

    def _qs(self) -> dict[str, list[str]]:
        parsed = urllib.parse.urlparse(self.path)
        return urllib.parse.parse_qs(parsed.query)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path in ("/api/health", "/health"):
            self._json(200, {"ok": True, "service": "guardian", "version": "0.3.0"})
            return
        if path == "/.well-known/mcp.json":
            self._json(200, discovery(f"http://0.0.0.0:{PORT}"))
            return
        if not self._authed():
            self._json(
                401, {"ok": False, "error": "set GUARDIAN_TOKEN and send Bearer"}
            )
            return
        if path in ("/", "/index.html"):
            self._send(
                200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8"
            )
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
        if path == "/api/config":
            cfg = load_config()
            raw = self._qs().get("raw", ["0"])[0] == "1"
            self._json(200, cfg if raw else redact(cfg))
            return
        if path == "/api/history":
            limit = int((self._qs().get("limit") or ["100"])[0])
            self._json(200, {"events": list_history(limit)})
            return
        if path == "/api/contract":
            self._json(200, _contract())
            return
        if path == "/api/combo":
            self._json(200, redact(agent_combo()))
            return
        if path in ("/api/models", "/api/schema"):
            self._json(200, build_inventory())
            return
        if path == "/api/skill":
            skill = OVERLAY / "skills" / "voiceeu-guardian" / "SKILL.md"
            text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
            self._send(200, text.encode("utf-8"), "text/markdown; charset=utf-8")
            return
        if path == "/api/mcp/tools":
            self._json(200, {"tools": TOOLS})
            return
        if path.startswith("/static/"):
            target = (STATIC / path[len("/static/") :]).resolve()
            if (
                not str(target).startswith(str(STATIC.resolve()))
                or not target.is_file()
            ):
                self._json(404, {"error": "not found"})
                return
            ctype = (
                "text/css" if target.suffix == ".css" else "application/octet-stream"
            )
            self._send(200, target.read_bytes(), ctype)
            return
        self._json(404, {"error": "not found"})

    def do_PUT(self) -> None:  # noqa: N802
        self._write_config()

    def do_POST(self) -> None:  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path == "/mcp":
            if not self._authed():
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            message = self._read_json()
            code, payload = handle_rpc(message)
            if payload is None:
                self._send(code, b"", "application/json")
                return
            self._json(code, payload)
            return
        if path == "/api/config":
            self._write_config()
            return
        self._json(404, {"error": "not found"})

    def _write_config(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path != "/api/config":
            self._json(404, {"error": "not found"})
            return
        if not self._authed():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "invalid json"})
            return
        actor = self.headers.get("X-Actor") or body.get("actor") or "guardian-ui"
        patch = body.get("config") if isinstance(body.get("config"), dict) else body
        saved = save_config(patch, actor=str(actor), source="http")
        self._json(200, {"ok": True, "config": redact(saved)})


def main() -> None:
    write_runtime_env()
    record_boot_snapshot()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"guardian listening on {HOST}:{PORT} api={DOGRAH_API} mcp=/mcp")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
