"""Pydantic schemas for Deepgram EU. Separate provider id from US Deepgram."""

from typing import Literal

from pydantic import Field, computed_field

from api.services.configuration.options import (
    DEEPGRAM_FLUX_MULTILINGUAL_LANGUAGE_OPTIONS,
    DEEPGRAM_LANGUAGES,
    DEEPGRAM_STT_MODELS,
)
from api.services.configuration.registry import (
    BaseServiceConfiguration,
    BaseSTTConfiguration,
    ServiceProviders,
    provider_model_config,
    register_stt,
    register_tts,
)
from custom.providers.deepgram_eu.config import DOCS_URL, PROVIDER_TITLE

DEEPGRAM_EU_PROVIDER_MODEL_CONFIG = provider_model_config(
    PROVIDER_TITLE,
    description=(
        "Deepgram speech models on the EU residency endpoint "
        "(api.eu.deepgram.com). Same API key as Deepgram US. "
        "Whisper models are not available in the EU — use Nova or Flux."
    ),
    provider_docs_url=DOCS_URL,
)


@register_stt
class DeepgramEUSTTConfiguration(BaseSTTConfiguration):
    model_config = DEEPGRAM_EU_PROVIDER_MODEL_CONFIG
    provider: Literal[ServiceProviders.DEEPGRAM_EU] = ServiceProviders.DEEPGRAM_EU
    model: str = Field(
        default="nova-3-general",
        description="Deepgram STT model (EU inference host).",
        json_schema_extra={"examples": DEEPGRAM_STT_MODELS, "allow_custom_input": True},
    )
    language: str = Field(
        default="multi",
        description=(
            "Language code. 'multi' enables Nova-3 auto-detect and omits "
            "language hints for Flux multilingual auto-detect."
        ),
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


@register_tts
class DeepgramEUTTSConfiguration(BaseServiceConfiguration):
    model_config = DEEPGRAM_EU_PROVIDER_MODEL_CONFIG
    provider: Literal[ServiceProviders.DEEPGRAM_EU] = ServiceProviders.DEEPGRAM_EU
    voice: str = Field(
        default="aura-2-helena-en",
        description="Deepgram voice ID (model is inferred from the 'aura-N' prefix).",
    )

    @computed_field
    @property
    def model(self) -> str:
        if "aura-1" in self.voice:
            return "aura-1"
        return "aura-2"
