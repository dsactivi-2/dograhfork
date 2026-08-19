"""Official Deepgram EU endpoint constants.

Source: https://developers.deepgram.com/reference/custom-endpoints
         https://developers.deepgram.com/reference/regional-endpoints

Same API keys as US. Whisper models are NOT available on the EU host.
"""

from __future__ import annotations

from typing import Any

PROVIDER_ID = "deepgram_eu"
PROVIDER_TITLE = "Deepgram EU"
DOCS_URL = "https://developers.deepgram.com/reference/custom-endpoints"

# Official regional host (no scheme).
STT_HOST = "api.eu.deepgram.com"

# REST / key-check / Nova HTTP
HTTP_BASE_URL = "https://api.eu.deepgram.com"

# Pipecat DeepgramTTSService(base_url=...) expects the WS origin (it appends /v1/speak).
WS_BASE_URL = "wss://api.eu.deepgram.com"

# Classic listen (docs). Pipecat Nova STT derives this from HTTP_BASE_URL.
LISTEN_V1_URL = "wss://api.eu.deepgram.com/v1/listen"

# Flux (Pipecat DeepgramFluxSTTService url= default is US /v2/listen).
FLUX_LISTEN_URL = "wss://api.eu.deepgram.com/v2/listen"

# Official TTS speak path (for docs / SDK). Pipecat gets WS_BASE_URL instead.
TTS_SPEAK_URL = "wss://api.eu.deepgram.com/v1/speak"


def build_eu_environment() -> Any:
    """Deepgram Python SDK v6/v7 environment for api.eu.deepgram.com.

    Official constructor is DeepgramClientEnvironment, not DeepgramEnvironment.
    v7 rejects a bare base_url on DeepgramClient.
    """
    try:
        from deepgram import DeepgramClientEnvironment
    except ImportError:
        from deepgram.environment import DeepgramClientEnvironment  # type: ignore

    kwargs: dict[str, str] = {
        "base": HTTP_BASE_URL,
        "production": WS_BASE_URL,
        "agent": WS_BASE_URL,
    }
    import inspect

    if "agent_rest" in inspect.signature(DeepgramClientEnvironment).parameters:
        kwargs["agent_rest"] = HTTP_BASE_URL
    return DeepgramClientEnvironment(**kwargs)
