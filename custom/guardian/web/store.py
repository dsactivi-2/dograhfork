"""Persisted Guardian config + append-only history. Survives image rebuilds."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

STATE = Path(os.environ.get("STATE_DIR", "/state"))
REPO = Path(os.environ.get("REPO_ROOT", "/probe"))
OVERLAY = Path(os.environ.get("OVERLAY_ROOT", str(REPO / "custom")))

SECRET_KEYS = ("api_key", "token", "password", "secret")

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "deepgram_base_url": "https://api.eu.deepgram.com",
    "default_stt": "deepgram_3",
    "default_tts": "fish_audio",
    "fish": {
        "api_key": "",
        "voice": "",
        "model": "s2.1-pro",
        "language": "de",
        "latency": "balanced",
        "speed": 1.0,
        "volume": 0,
        "normalize": True,
    },
    "deepgram_stt": {
        "api_key": "",
        "provider": "deepgram_3",
        "model": "nova-3-general",
        "language": "multi",
    },
    "integrations": {
        "telnyx": {"enabled": True, "notes": "official Dograh provider — do not fork"},
        "step2job": {"url": "", "notes": ""},
        "agents": {"url": "", "notes": ""},
    },
    "notes": "",
    "llm": {
        "provider": "openai",
        "model": "gpt-4.1",
        "temperature": None,
        "max_tokens": None,
        "wrapper": False,
    },
    "prompts": {
        "agent_system_prompt": "",
        "start_call_prompt": "",
        "end_call_prompt": "",
        "qa_system_prompt": "",
    },
    "factory": {
        "deepgram": {
            "wrapper": False,
            "endpointing": 100,
            "smart_format": False,
            "punctuate": False,
            "numerals": False,
            "interim_results": False,
            "diarize": False,
            "vad_events": False,
            "keyterm_from_workflow": True,
            "utterance_end_ms": False,
            "profanity_filter": False,
            "should_interrupt": False,
            "reads_DEEPGRAM_BASE_URL": False,
        },
        "deepgram_eu": {
            "wrapper": True,
            "endpointing": 100,
            "smart_format": False,
            "punctuate": False,
            "numerals": False,
            "interim_results": False,
            "diarize": False,
            "vad_events": False,
            "keyterm_from_workflow": True,
            "utterance_end_ms": False,
            "profanity_filter": False,
            "should_interrupt": False,
            "reads_DEEPGRAM_BASE_URL": False,
            "fixed_eu_host": True,
        },
        "deepgram_2": {
            "wrapper": True,
            "endpointing": 100,
            "smart_format": True,
            "punctuate": True,
            "numerals": False,
            "interim_results": True,
            "diarize": False,
            "vad_events": False,
            "keyterm_from_workflow": True,
            "utterance_end_ms": False,
            "profanity_filter": False,
            "should_interrupt": False,
            "reads_DEEPGRAM_BASE_URL": True,
        },
        "deepgram_3": {
            "wrapper": True,
            "endpointing": 400,
            "smart_format": True,
            "punctuate": True,
            "numerals": True,
            "interim_results": False,
            "diarize": False,
            "vad_events": True,
            "keyterm_from_workflow": False,
            "utterance_end_ms": False,
            "profanity_filter": False,
            "should_interrupt": False,
            "reads_DEEPGRAM_BASE_URL": True,
        },
        "fish_audio": {
            "wrapper": True,
            "output_format_pcm": True,
            "sample_rate_from_pipeline": True,
            "voice_required": True,
            "xml_function_tag_filter": True,
            "skip_recording_aggregator": True,
            "silence_time_s": 1.0,
            "invalid_latency_falls_back_balanced": True,
            "reads_FISH_ENV": False,
        },
    },
}


def _ensure() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "snapshots").mkdir(exist_ok=True)


def config_path() -> Path:
    return STATE / "config.json"


def history_path() -> Path:
    return STATE / "history.jsonl"


def runtime_env_path() -> Path:
    return STATE / "runtime.env"


def load_config() -> dict[str, Any]:
    _ensure()
    path = config_path()
    if not path.is_file():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    data = json.loads(path.read_text(encoding="utf-8"))
    return _merge(DEFAULT_CONFIG, data)


def _merge(base: Any, over: Any) -> Any:
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for key, val in over.items():
            out[key] = _merge(base[key], val) if key in base else val
        return out
    return over


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("***" if any(s in k.lower() for s in SECRET_KEYS) and v else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def save_config(next_cfg: dict[str, Any], *, actor: str, source: str) -> dict[str, Any]:
    _ensure()
    before = load_config()
    merged = _merge(DEFAULT_CONFIG, next_cfg)
    config_path().write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    write_runtime_env(merged)
    changed = _diff(redact(before), redact(merged))
    append_history(
        {
            "action": "config.set",
            "actor": actor,
            "source": source,
            "summary": ", ".join(changed) or "no field change",
            "changed": changed,
            "before": redact(before),
            "after": redact(merged),
        }
    )
    return merged


def write_runtime_env(cfg: dict[str, Any] | None = None) -> Path:
    _ensure()
    cfg = cfg or load_config()
    url = str(cfg.get("deepgram_base_url") or "https://api.eu.deepgram.com").rstrip("/")
    runtime_env_path().write_text(
        f"# generated by Guardian — do not edit by hand\nDEEPGRAM_BASE_URL={url}\n",
        encoding="utf-8",
    )
    return runtime_env_path()


def append_history(event: dict[str, Any]) -> dict[str, Any]:
    _ensure()
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "id": hashlib.sha1(f"{time.time_ns()}".encode()).hexdigest()[:12],
        **event,
    }
    with history_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def list_history(limit: int = 100) -> list[dict[str, Any]]:
    path = history_path()
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines[-max(limit, 1) :]:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.reverse()
    return rows


def _diff(before: Any, after: Any, prefix: str = "") -> list[str]:
    if before == after:
        return []
    if not isinstance(before, dict) or not isinstance(after, dict):
        return [prefix or "value"]
    keys = set(before) | set(after)
    found: list[str] = []
    for key in sorted(keys):
        path = f"{prefix}.{key}" if prefix else key
        if key not in before:
            found.append(path)
        elif key not in after:
            found.append(path)
        else:
            found.extend(_diff(before[key], after[key], path))
    return found


def hash_tree() -> dict[str, str]:
    hashes: dict[str, str] = {}
    roots = [OVERLAY]
    for seam in (
        REPO / "api" / "services" / "configuration" / "registry.py",
        REPO / "api" / "services" / "pipecat" / "service_factory.py",
        REPO / "api" / "services" / "configuration" / "check_validity.py",
        REPO / "api" / "Dockerfile",
        REPO / "api" / "services" / "configuration" / "options" / "deepgram.py",
    ):
        if seam.is_file():
            rel = (
                str(seam.relative_to(REPO))
                if str(seam).startswith(str(REPO))
                else seam.name
            )
            hashes[rel] = hashlib.sha256(seam.read_bytes()).hexdigest()[:16]
    if OVERLAY.is_dir():
        for path in sorted(OVERLAY.rglob("*")):
            if not path.is_file():
                continue
            if any(
                part in {".git", "__pycache__", "state", "snapshots"}
                for part in path.parts
            ):
                continue
            rel = str(path.relative_to(OVERLAY.parent))
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return hashes


def record_boot_snapshot(actor: str = "guardian") -> dict[str, Any] | None:
    _ensure()
    current = hash_tree()
    snap = STATE / "snapshots" / "last.json"
    previous = json.loads(snap.read_text(encoding="utf-8")) if snap.is_file() else {}
    snap.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    if not previous:
        append_history(
            {
                "action": "snapshot.init",
                "actor": actor,
                "source": "boot",
                "summary": f"first snapshot ({len(current)} files)",
                "changed": [],
            }
        )
        return None
    added = sorted(set(current) - set(previous))
    removed = sorted(set(previous) - set(current))
    changed = sorted(
        k for k in set(current) & set(previous) if current[k] != previous[k]
    )
    if not added and not removed and not changed:
        return None
    event = append_history(
        {
            "action": "deploy.diff",
            "actor": actor,
            "source": "boot",
            "summary": f"deploy/overwrite: +{len(added)} ~{len(changed)} -{len(removed)}",
            "added": added,
            "removed": removed,
            "changed": changed,
        }
    )
    return event


def agent_combo(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    fish = cfg["fish"]
    stt = cfg["deepgram_stt"]
    llm = cfg.get("llm") or {}
    prompts = cfg.get("prompts") or {}
    factory = cfg.get("factory") or {}
    return {
        "stt": {
            "provider": stt.get("provider") or cfg.get("default_stt"),
            "api_key": stt.get("api_key") or "",
            "model": stt.get("model"),
            "language": stt.get("language"),
        },
        "tts": {
            "provider": cfg.get("default_tts"),
            "api_key": fish.get("api_key") or "",
            "model": fish.get("model"),
            "voice": fish.get("voice") or "",
            "language": fish.get("language"),
            "latency": fish.get("latency"),
            "speed": fish.get("speed"),
            "volume": fish.get("volume"),
            "normalize": fish.get("normalize"),
        },
        "llm": {
            "provider": llm.get("provider") or "",
            "model": llm.get("model") or "",
            "temperature": llm.get("temperature"),
            "max_tokens": llm.get("max_tokens"),
            "wrapper": bool(llm.get("wrapper")),
        },
        "prompts": {
            "agent_system_prompt": prompts.get("agent_system_prompt") or "",
            "start_call_prompt": prompts.get("start_call_prompt") or "",
            "end_call_prompt": prompts.get("end_call_prompt") or "",
            "qa_system_prompt": prompts.get("qa_system_prompt") or "",
            "agent_system_prompt_set": bool(prompts.get("agent_system_prompt")),
            "start_call_prompt_set": bool(prompts.get("start_call_prompt")),
            "end_call_prompt_set": bool(prompts.get("end_call_prompt")),
            "qa_system_prompt_set": bool(prompts.get("qa_system_prompt")),
        },
        "factory": factory,
    }
