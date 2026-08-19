"""STT schema for Deepgram 3. Sibling of official deepgram — not a patch."""

from typing import Literal

from pydantic import Field

from api.services.configuration.options import (
    DEEPGRAM_FLUX_MULTILINGUAL_LANGUAGE_OPTIONS,
    DEEPGRAM_LANGUAGES,
    DEEPGRAM_STT_MODELS,
)
from api.services.configuration.registry import (
    BaseSTTConfiguration,
    ServiceProviders,
    provider_model_config,
    register_stt,
)
from custom.providers.deepgram_3.config import DOCS_URL, PROVIDER_TITLE, STT_DEFAULTS
from custom.providers.deepgram_common import LIVE_STT_DEFAULTS

DEEPGRAM_3_CONFIG = provider_model_config(
    PROVIDER_TITLE,
    description=(
        "Nova-3 live-agent defaults matching Deepgram 2 (endpointing 100ms, "
        "diarize, keyterm prompting) plus numerals/vad_events. "
        "Inference host follows DEEPGRAM_BASE_URL. Typical pair: Fish Audio TTS."
    ),
    provider_docs_url=DOCS_URL,
)


@register_stt
class Deepgram3STTConfiguration(BaseSTTConfiguration):
    model_config = DEEPGRAM_3_CONFIG
    provider: Literal[ServiceProviders.DEEPGRAM_3] = ServiceProviders.DEEPGRAM_3
    model: str = Field(
        default="nova-3-general",
        description="Deepgram STT model (Nova-3 or Flux).",
        json_schema_extra={"examples": DEEPGRAM_STT_MODELS, "allow_custom_input": True},
    )
    language: str = Field(
        default="multi",
        description="Language code. Nova-3 auto-detect uses 'multi'. Flux-EN only 'en'.",
        json_schema_extra={
            "examples": DEEPGRAM_LANGUAGES,
            "allow_custom_input": True,
            "model_options": {
                "nova-3-general": DEEPGRAM_LANGUAGES,
                "nova-3-medical": DEEPGRAM_LANGUAGES,
                "flux-general-en": ("en",),
                "flux-general-multi": DEEPGRAM_FLUX_MULTILINGUAL_LANGUAGE_OPTIONS,
            },
        },
    )
    smart_format: bool = Field(
        default=LIVE_STT_DEFAULTS["smart_format"],
        description="Normalize numbers, dates, and punctuation.",
    )
    interim_results: bool = Field(
        default=LIVE_STT_DEFAULTS["interim_results"],
        description="Emit partial transcripts while the speaker is talking.",
    )
    endpointing: bool = Field(
        default=LIVE_STT_DEFAULTS["endpointing"],
        description="Detect end of utterance (100ms when on).",
    )
    keyterm_prompting: bool = Field(
        default=LIVE_STT_DEFAULTS["keyterm_prompting"],
        description="Boost workflow keyterms in recognition.",
    )
    diarize: bool = Field(
        default=LIVE_STT_DEFAULTS["diarize"],
        description="Separate speakers.",
    )
    punctuate: bool = Field(
        default=LIVE_STT_DEFAULTS["punctuate"],
        description="Add punctuation to the transcript.",
    )
    profanity_filter: bool = Field(
        default=LIVE_STT_DEFAULTS["profanity_filter"],
        description="Filter profanity from the transcript.",
    )
    redact: bool = Field(
        default=LIVE_STT_DEFAULTS["redact"],
        description="Redact PII / sensitive spans.",
    )
    replace: bool = Field(
        default=LIVE_STT_DEFAULTS["replace"],
        description="Enable Find and Replace on the transcript.",
    )
    numerals: bool = Field(
        default=STT_DEFAULTS["numerals"],
        description="Convert spoken numbers to numerals.",
    )
    vad_events: bool = Field(
        default=STT_DEFAULTS["vad_events"],
        description="Emit Deepgram VAD events.",
    )
