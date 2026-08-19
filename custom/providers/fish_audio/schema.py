"""Fish Audio TTS schema. Lives only in custom/ — never patch registry.py classes."""

from typing import Literal

from pydantic import Field

from api.services.configuration.registry import (
    BaseTTSConfiguration,
    ServiceProviders,
    provider_model_config,
    register_tts,
)
from custom.providers.fish_audio.config import (
    DOCS_URL,
    LATENCY_MODES,
    PROVIDER_TITLE,
    TTS_LANGUAGES,
    TTS_MODELS,
)

FISH_AUDIO_PROVIDER_MODEL_CONFIG = provider_model_config(
    PROVIDER_TITLE,
    description=(
        "Fish Audio streaming TTS with expressive voices, open-domain emotion "
        "tags, and multilingual synthesis (including Bosnian/Croatian/Serbian)."
    ),
    provider_docs_url=DOCS_URL,
)


@register_tts
class FishAudioTTSConfiguration(BaseTTSConfiguration):
    model_config = FISH_AUDIO_PROVIDER_MODEL_CONFIG
    provider: Literal[ServiceProviders.FISH_AUDIO] = ServiceProviders.FISH_AUDIO
    model: str = Field(
        default="s2-pro",
        description=(
            "Fish Audio TTS model. s2-pro / s2.1-pro are production models; "
            "s2.1-pro-free is free under fair use for prototyping."
        ),
        json_schema_extra={
            "examples": TTS_MODELS,
            "allow_custom_input": True,
        },
    )
    voice: str = Field(
        description=(
            "Fish Audio voice / reference ID from your Fish Audio library "
            "(opaque ID from the dashboard or search_voices API)."
        ),
        json_schema_extra={"allow_custom_input": True},
    )
    language: str = Field(
        default="en",
        description=(
            "Language hint for synthesis (ISO 639-1). Auto-detection works for "
            "most languages including Bosnian (bs), Croatian (hr), Serbian (sr)."
        ),
        json_schema_extra={
            "examples": TTS_LANGUAGES,
            "allow_custom_input": True,
        },
    )
    latency: str = Field(
        default="balanced",
        description=(
            "Latency mode for streaming synthesis. 'balanced' is more stable "
            "(recommended for telephony); 'normal' prioritizes lower latency."
        ),
        json_schema_extra={"examples": LATENCY_MODES},
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Prosody speed multiplier (0.5 to 2.0).",
    )
    volume: int = Field(
        default=0,
        ge=-20,
        le=20,
        description="Prosody volume adjustment in dB (-20 to 20).",
    )
    normalize: bool = Field(
        default=True,
        description="Whether Fish Audio should normalize output audio levels.",
    )
