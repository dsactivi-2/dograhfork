"""Complete schema inventory: every field, including false / unset.

Parses registry.py + overlay schemas with AST so the slim Guardian
container does not need pydantic or the Dograh API package.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from store import OVERLAY, REPO, load_config, redact

# Every factory flag we know about — never drop a False.
FACTORY_FLAGS: dict[str, dict[str, Any]] = {
    "deepgram": {
        "wrapper": False,
        "wrapper_module": "api/services/pipecat/service_factory.py",
        "flags": {
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
    },
    "deepgram_eu": {
        "wrapper": True,
        "wrapper_module": "custom/providers/deepgram_eu/factory.py",
        "flags": {
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
    },
    "deepgram_2": {
        "wrapper": True,
        "wrapper_module": "custom/providers/deepgram_2/factory.py",
        "flags": {
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
    },
    "deepgram_3": {
        "wrapper": True,
        "wrapper_module": "custom/providers/deepgram_3/factory.py",
        "flags": {
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
    },
    "fish_audio": {
        "wrapper": True,
        "wrapper_module": "custom/providers/fish_audio/factory.py",
        "flags": {
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
    "minimax": {
        "wrapper": True,
        "wrapper_module": "api/services/pipecat/minimax_tts.py",
        "flags": {"owned_session_cleanup": True},
    },
    "grok_realtime": {
        "wrapper": True,
        "wrapper_module": "api/services/pipecat/realtime/grok_realtime.py",
        "flags": {"openai_realtime_shim": True},
    },
    "ultravox_realtime": {
        "wrapper": True,
        "wrapper_module": "api/services/pipecat/realtime/ultravox_realtime.py",
        "flags": {"history_adapter": True},
    },
}

PROMPT_SLOTS = [
    {
        "id": "agent_system_prompt",
        "where": "Workflow agent node field `prompt` → compose_system_prompt_for_node",
        "file": "api/services/workflow/pipecat_engine.py",
    },
    {
        "id": "start_call_prompt",
        "where": "Start-call node prompt",
        "file": "workflow definition (Dograh UI)",
    },
    {
        "id": "end_call_prompt",
        "where": "End-call node prompt",
        "file": "workflow definition (Dograh UI)",
    },
    {
        "id": "qa_system_prompt",
        "where": "QA node qa_system_prompt",
        "file": "api/services/workflow/dto.py",
    },
]


def _literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in {"True", "False", "None"}:
        return {"True": True, "False": False, "None": None}[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        val = _literal(node.operand)
        return -val if isinstance(val, (int, float)) else None
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [_literal(elt) for elt in node.elts]
    if isinstance(node, ast.Dict):
        return {
            _literal(k): _literal(v)
            for k, v in zip(node.keys, node.values)
            if k is not None
        }
    if isinstance(node, ast.Attribute):
        return ast.unparse(node)
    if isinstance(node, ast.Name):
        return node.id
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return None


def _type_str(node: ast.AST | None) -> str:
    if node is None:
        return "any"
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return "any"


def _field_from_ann(stmt: ast.AnnAssign) -> dict[str, Any] | None:
    if not isinstance(stmt.target, ast.Name):
        return None
    name = stmt.target.id
    if name in {"model_config"}:
        return None
    info: dict[str, Any] = {
        "name": name,
        "type": _type_str(stmt.annotation),
        "required": True,
        "default": None,
        "description": "",
        "examples": [],
        "has_default": False,
    }
    value = stmt.value
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "Field":
        kwargs = {kw.arg: _literal(kw.value) for kw in value.keywords if kw.arg}
        if value.args:
            kwargs.setdefault("default", _literal(value.args[0]))
        if "default" in kwargs:
            info["default"] = kwargs["default"]
            info["has_default"] = True
            info["required"] = kwargs["default"] is None and "default_factory" not in kwargs
        if "default_factory" in kwargs:
            info["has_default"] = True
            info["required"] = False
        info["description"] = kwargs.get("description") or ""
        extra = kwargs.get("json_schema_extra") or {}
        if isinstance(extra, dict):
            info["examples"] = extra.get("examples") or extra.get("model_options") or []
            info["allow_custom_input"] = bool(extra.get("allow_custom_input", False))
        if "ge" in kwargs:
            info["ge"] = kwargs["ge"]
        if "le" in kwargs:
            info["le"] = kwargs["le"]
        if "gt" in kwargs:
            info["gt"] = kwargs["gt"]
    elif value is not None:
        info["default"] = _literal(value)
        info["has_default"] = True
        info["required"] = False
    return info


def _decorator_kind(decs: list[ast.expr]) -> str | None:
    for dec in decs:
        if isinstance(dec, ast.Name) and dec.id.startswith("register_"):
            return dec.id.replace("register_", "")
        if isinstance(dec, ast.Attribute) and dec.attr.startswith("register_"):
            return dec.attr.replace("register_", "")
        if isinstance(dec, ast.Call):
            func = dec.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name == "register_service" and dec.args:
                arg = ast.unparse(dec.args[0])
                if "REALTIME" in arg:
                    return "realtime"
                if "LLM" in arg:
                    return "llm"
    return None


def _provider_id(fields: list[dict[str, Any]]) -> str | None:
    for field in fields:
        if field["name"] != "provider":
            continue
        default = field.get("default")
        if isinstance(default, str) and "ServiceProviders." in default:
            return default.split(".")[-1].lower()
        if isinstance(default, str):
            return default
        typ = field.get("type") or ""
        if "ServiceProviders." in typ:
            return typ.split("ServiceProviders.")[-1].split("]")[0].split(",")[0].strip().lower()
    return None


def parse_schema_file(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        kind = _decorator_kind(node.decorator_list)
        if not kind:
            continue
        fields = []
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign):
                item = _field_from_ann(stmt)
                if item:
                    fields.append(item)
        provider = _provider_id(fields) or node.name.lower()
        out.append(
            {
                "class": node.name,
                "kind": kind,
                "provider": provider,
                "origin": "overlay" if "custom/" in str(path).replace("\\", "/") else "upstream",
                "file": _rel(path),
                "fields": fields,
            }
        )
    return out


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except Exception:  # noqa: BLE001
        return str(path)


def collect_classes() -> list[dict[str, Any]]:
    classes: list[dict[str, Any]] = []
    registry = REPO / "api" / "services" / "configuration" / "registry.py"
    classes.extend(parse_schema_file(registry))
    if OVERLAY.is_dir():
        for schema in sorted((OVERLAY / "providers").glob("*/schema.py")):
            classes.extend(parse_schema_file(schema))
    return classes


def _current_for(provider: str, field: str, cfg: dict[str, Any]) -> Any:
    if provider in {"deepgram_2", "deepgram_3", "deepgram_eu", "deepgram"} and field in (
        cfg.get("deepgram_stt") or {}
    ):
        if (cfg.get("deepgram_stt") or {}).get("provider") == provider or field != "provider":
            if provider == (cfg.get("deepgram_stt") or {}).get("provider") or field in {
                "api_key",
                "model",
                "language",
            }:
                return (cfg.get("deepgram_stt") or {}).get(field)
    if provider == "fish_audio":
        return (cfg.get("fish") or {}).get(field)
    if provider == (cfg.get("llm") or {}).get("provider"):
        return (cfg.get("llm") or {}).get(field)
    return None


def _field_row(field: dict[str, Any], current: Any) -> dict[str, Any]:
    default = field.get("default")
    has_current = current is not None and current != "" and current != []
    value = current if has_current else default
    return {
        "name": field["name"],
        "type": field["type"],
        "required": bool(field.get("required")),
        "has_default": bool(field.get("has_default")),
        "default": default,
        "current": value,
        "set": has_current and current != default,
        "description": field.get("description") or "",
        "examples": field.get("examples") or [],
        "ge": field.get("ge"),
        "le": field.get("le"),
        "gt": field.get("gt"),
        "allow_custom_input": bool(field.get("allow_custom_input")),
    }


def _flag_rows(flags: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, value in flags.items():
        rows.append(
            {
                "name": name,
                "type": type(value).__name__,
                "required": False,
                "has_default": True,
                "default": value,
                "current": value,
                "set": False,
                "locked": True,
                "source": "factory",
                "description": "Factory-verdrahtet — nicht in der Dograh-UI.",
            }
        )
    return rows


def build_inventory(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    classes = collect_classes()
    models = []
    for item in classes:
        provider = item["provider"]
        factory = FACTORY_FLAGS.get(provider, {"wrapper": False, "wrapper_module": "", "flags": {}})
        ui_fields = [_field_row(f, _current_for(provider, f["name"], cfg)) for f in item["fields"]]
        factory_fields = _flag_rows(factory.get("flags") or {})
        has_temp = any(f["name"] == "temperature" for f in ui_fields)
        models.append(
            {
                "provider": provider,
                "kind": item["kind"],
                "class": item["class"],
                "origin": item["origin"],
                "file": item["file"],
                "wrapper": {
                    "used": bool(factory.get("wrapper")),
                    "module": factory.get("wrapper_module") or "",
                },
                "has_temperature": has_temp,
                "temperature": next((f["current"] for f in ui_fields if f["name"] == "temperature"), None),
                "ui_fields": ui_fields,
                "factory_fields": factory_fields,
                "all_fields": ui_fields + factory_fields,
            }
        )

    prompts_cfg = cfg.get("prompts") or {}
    prompts = []
    for slot in PROMPT_SLOTS:
        text = prompts_cfg.get(slot["id"]) or ""
        prompts.append(
            {
                **slot,
                "set": bool(text),
                "empty": not bool(text),
                "current": text,
                "default": "",
            }
        )

    llm = cfg.get("llm") or {}
    return {
        "version": "0.4.0",
        "rule": "Every field is listed. false / unset / empty stay visible.",
        "counts": {
            "models": len(models),
            "llm": sum(1 for m in models if m["kind"] == "llm"),
            "stt": sum(1 for m in models if m["kind"] == "stt"),
            "tts": sum(1 for m in models if m["kind"] == "tts"),
            "realtime": sum(1 for m in models if m["kind"] == "realtime"),
            "embeddings": sum(1 for m in models if m["kind"] == "embeddings"),
            "wrappers_on": sum(1 for m in models if m["wrapper"]["used"]),
        },
        "llm_active": {
            "provider": llm.get("provider") or "",
            "model": llm.get("model") or "",
            "temperature": llm.get("temperature"),
            "temperature_supported": llm.get("temperature") is not None
            or any(
                m["provider"] == (llm.get("provider") or "") and m["has_temperature"]
                for m in models
            ),
            "wrapper": False,
            "system_prompt": (cfg.get("prompts") or {}).get("agent_system_prompt") or "",
        },
        "prompts": prompts,
        "models": models,
        "config": redact(cfg),
    }


def dump_catalog(path: Path | None = None) -> Path:
    target = path or (OVERLAY / "contract" / "schema_catalog.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_inventory()
    # Strip live secrets-bearing config from the committed catalog
    payload.pop("config", None)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return target
