"""Shared Deepgram overlay helpers. Official US Deepgram does not import this."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from deepgram import DeepgramClient

DEFAULT_US_HOST = "api.deepgram.com"
DEFAULT_EU_HOST = "api.eu.deepgram.com"

_FLUX_MODELS = {"flux-general-en", "flux-general-multi"}


def normalize_host(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value:
        return DEFAULT_US_HOST
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
