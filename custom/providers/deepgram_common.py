"""Shared Deepgram overlay helpers. Official US Deepgram does not import this."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from deepgram import DeepgramClient

DEFAULT_US_HOST = "api.deepgram.com"
DEFAULT_EU_HOST = "api.eu.deepgram.com"

_FLUX_MODELS = {"flux-general-en", "flux-general-multi"}

# Live-agent Listen flags for Deepgram 2/3 wrappers. Endpointing "on" is 100ms.
LIVE_STT_DEFAULTS = {
    "smart_format": True,
    "interim_results": False,
    "endpointing": True,
    "endpointing_ms": 100,
    "keyterm_prompting": True,
    "diarize": True,
    "punctuate": True,
    "profanity_filter": False,
    "redact": False,
    "replace": True,
}

_LIVE_BOOL_KEYS = (
    "smart_format",
    "interim_results",
    "keyterm_prompting",
    "diarize",
    "punctuate",
    "profanity_filter",
    "redact",
    "replace",
)


def normalize_host(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value:
        return DEFAULT_EU_HOST
    if "://" not in value:
        value = "https://" + value
    host = urlparse(value).hostname
    return host or DEFAULT_US_HOST


def deepgram_inference_urls(*, force_host: str | None = None) -> dict[str, str]:
    """STT/TTS/Flux hosts. Key checks stay on the US management API."""
    host = normalize_host(force_host or os.environ.get("DEEPGRAM_BASE_URL"))
    return {
        "host": host,
        "stt_host": host,
        "flux_listen": f"wss://{host}/v2/listen",
        "tts_ws": f"wss://{host}",
    }


def is_flux_model(model: str | None) -> bool:
    return (model or "") in _FLUX_MODELS


def live_flag(stt, name: str):
    return getattr(stt, name, LIVE_STT_DEFAULTS[name])


def resolve_endpointing(stt) -> int | bool:
    raw = getattr(stt, "endpointing", LIVE_STT_DEFAULTS["endpointing"])
    if raw is True:
        return LIVE_STT_DEFAULTS["endpointing_ms"]
    if raw is False:
        return False
    if raw is None:
        return LIVE_STT_DEFAULTS["endpointing_ms"]
    return raw


def live_stt_settings_kwargs(
    user_config, *, model: str, language: str, keyterms=None
) -> dict:
    """Pipecat DeepgramSTTSettings kwargs for the Deepgram 2/3 live profile."""
    stt = user_config.stt
    flags = {name: live_flag(stt, name) for name in _LIVE_BOOL_KEYS}
    keyterm = (keyterms or []) if flags["keyterm_prompting"] else []
    return {
        "language": language,
        "model": model,
        "smart_format": flags["smart_format"],
        "interim_results": flags["interim_results"],
        "endpointing": resolve_endpointing(stt),
        "diarize": flags["diarize"],
        "punctuate": flags["punctuate"],
        "profanity_filter": flags["profanity_filter"],
        "keyterm": keyterm,
        "extra": {
            "redact": flags["redact"],
            "replace": flags["replace"],
        },
    }


def check_deepgram_management_key(api_key: str) -> bool:
    """Always hits US management. Inference region is a separate concern."""
    try:
        client = DeepgramClient(api_key=api_key)
        client.manage.v1.projects.list()
        return True
    except Exception as exc:
        raise ValueError(
            "Invalid Deepgram API key (US management API at api.deepgram.com). "
            "Inference may still use DEEPGRAM_BASE_URL / Deepgram EU. "
            f"Detail: {exc}"
        ) from exc
