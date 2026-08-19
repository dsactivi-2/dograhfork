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
from custom.providers.deepgram_3.config import DOCS_URL, PROVIDER_TITLE

DEEPGRAM_3_CONFIG = provider_model_config(
    PROVIDER_TITLE,
    description=(
        "Nova-3 live-agent defaults: endpointing=400, vad_events, no keyterms. "
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
