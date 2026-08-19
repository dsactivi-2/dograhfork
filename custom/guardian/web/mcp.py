"""MCP JSON-RPC over HTTP so any agent can bind to Guardian."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from store import (
    REPO,
    agent_combo,
    list_history,
    load_config,
    redact,
    save_config,
)

import os

CONTRACT = Path(os.environ.get("OVERLAY_ROOT", "/probe/custom")) / "contract" / "overlay.json"
SKILL = (
    Path(os.environ.get("OVERLAY_ROOT", "/probe/custom"))
    / "skills"
    / "voiceeu-guardian"
    / "SKILL.md"
)


def _read_contract() -> dict[str, Any]:
    if CONTRACT.is_file():
        return json.loads(CONTRACT.read_text(encoding="utf-8"))
    return {"error": "contract missing"}


def _read_skill() -> str:
    if SKILL.is_file():
        return SKILL.read_text(encoding="utf-8")
    return "SKILL.md missing — overlay not mounted."


def _ok(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def tool_status(_: dict[str, Any]) -> dict[str, Any]:
    from app import snapshot

    return _ok(json.dumps(snapshot(), indent=2))


def tool_config_get(_: dict[str, Any]) -> dict[str, Any]:
    return _ok(json.dumps(redact(load_config()), indent=2))


def tool_config_set(args: dict[str, Any]) -> dict[str, Any]:
    patch = args.get("config") or args
    if not isinstance(patch, dict):
        return {"isError": True, "content": [{"type": "text", "text": "config must be an object"}]}
    actor = str(args.get("actor") or "mcp-agent")
    saved = save_config(patch, actor=actor, source="mcp")
    return _ok(json.dumps({"ok": True, "redacted": redact(saved)}, indent=2))


def tool_history(args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit") or 50)
    return _ok(json.dumps(list_history(limit), indent=2))


def tool_contract(_: dict[str, Any]) -> dict[str, Any]:
    return _ok(json.dumps(_read_contract(), indent=2))


def tool_combo(_: dict[str, Any]) -> dict[str, Any]:
    return _ok(json.dumps(redact(agent_combo()), indent=2))


def tool_skill(_: dict[str, Any]) -> dict[str, Any]:
    return _ok(_read_skill())


def tool_paths(_: dict[str, Any]) -> dict[str, Any]:
    contract = _read_contract()
    return _ok(json.dumps(contract.get("paths", {}), indent=2))


def tool_models(_: dict[str, Any]) -> dict[str, Any]:
    from inventory import build_inventory

    return _ok(json.dumps(build_inventory(), indent=2, default=str))


def tool_diagnose(_: dict[str, Any]) -> dict[str, Any]:
    from app import run_healthcheck

    return _ok(json.dumps(run_healthcheck(), indent=2))


TOOLS: list[dict[str, Any]] = [
    {
        "name": "guardian_status",
        "description": "Live Dograh + overlay health, providers, wiring.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_config_get",
        "description": "Read overlay config (secrets redacted).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_config_set",
        "description": "Patch overlay config. Recorded in history. Writes runtime.env.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor": {"type": "string"},
                "config": {"type": "object", "description": "Partial config to merge"},
            },
        },
    },
    {
        "name": "guardian_history",
        "description": "What changed when. Use after a deploy overwrite.",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 50}},
        },
    },
    {
        "name": "guardian_contract",
        "description": "Paths, seams, providers, factory locks, rules.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_agent_combo",
        "description": "Typical VoiceEU agent JSON (deepgram_3 + fish_audio).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_skill",
        "description": "How an agent must call Guardian and what it may not touch.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_paths",
        "description": "Where every overlay file must live.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_diagnose",
        "description": "Run overlay healthcheck (seams, forbidden US Deepgram edits).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "guardian_models",
        "description": "Every model/tool field in the repo, including false/unset, wrappers, temperature, prompts.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "guardian_status": tool_status,
    "guardian_config_get": tool_config_get,
    "guardian_config_set": tool_config_set,
    "guardian_history": tool_history,
    "guardian_contract": tool_contract,
    "guardian_agent_combo": tool_combo,
    "guardian_skill": tool_skill,
    "guardian_paths": tool_paths,
    "guardian_diagnose": tool_diagnose,
    "guardian_models": tool_models,
}

RESOURCES = [
    {"uri": "guardian://contract", "name": "Overlay contract", "mimeType": "application/json"},
    {"uri": "guardian://config", "name": "Live config", "mimeType": "application/json"},
    {"uri": "guardian://history", "name": "Change history", "mimeType": "application/json"},
    {"uri": "guardian://skill", "name": "Agent skill", "mimeType": "text/markdown"},
]


def handle_rpc(message: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
    method = message.get("method")
    rpc_id = message.get("id")
    params = message.get("params") or {}

    if method == "notifications/initialized" or method == "notifications/cancelled":
        return 204, None

    if method == "initialize":
        return 200, {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "voiceeu-guardian", "version": "0.3.0"},
            },
        }

    if method == "ping":
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {}}

    if method == "tools/list":
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if not handler:
            return 200, {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": f"unknown tool {name}"},
            }
        try:
            result = handler(args if isinstance(args, dict) else {})
        except Exception as exc:  # noqa: BLE001
            result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": result}

    if method == "resources/list":
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"resources": RESOURCES}}

    if method == "resources/read":
        uri = params.get("uri")
        text = _resource(uri)
        return 200, {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {"contents": [{"uri": uri, "mimeType": "text/plain", "text": text}]},
        }

    return 200, {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": -32601, "message": f"unknown method {method}"},
    }


def _resource(uri: str) -> str:
    if uri == "guardian://contract":
        return json.dumps(_read_contract(), indent=2)
    if uri == "guardian://config":
        return json.dumps(redact(load_config()), indent=2)
    if uri == "guardian://history":
        return json.dumps(list_history(100), indent=2)
    if uri == "guardian://skill":
        return _read_skill()
    return f"unknown resource {uri}"


def discovery(public_base: str) -> dict[str, Any]:
    return {
        "name": "voiceeu-guardian",
        "version": "0.3.0",
        "description": "VoiceEU overlay control plane for Dograh. Config, history, seams.",
        "transport": {"type": "http", "url": f"{public_base}/mcp"},
        "auth": "Authorization: Bearer $GUARDIAN_TOKEN (optional if token unset)",
        "tools": [t["name"] for t in TOOLS],
        "resources": [r["uri"] for r in RESOURCES],
        "skill": str(SKILL),
        "repo_hint": str(REPO),
    }
