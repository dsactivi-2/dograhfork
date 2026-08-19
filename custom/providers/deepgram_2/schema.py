"""STT schema for Deepgram 2. Sibling of official deepgram — not a patch."""

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
from custom.providers.deepgram_2.config import DOCS_URL, PROVIDER_TITLE

DEEPGRAM_2_CONFIG = provider_model_config(
    PROVIDER_TITLE,
    description=(
        "Deepgram live-agent profile: interim_results, smart_format, punctuate. "
        "Inference host follows DEEPGRAM_BASE_URL (US default, or EU)."
    ),
    provider_docs_url=DOCS_URL,
)


@register_stt
class Deepgram2STTConfiguration(BaseSTTConfiguration):
    model_config = DEEPGRAM_2_CONFIG
    provider: Literal[ServiceProviders.DEEPGRAM_2] = ServiceProviders.DEEPGRAM_2
    model: str = Field(
        default="nova-3-general",
        description="Deepgram STT model.",
        json_schema_extra={"examples": DEEPGRAM_STT_MODELS, "allow_custom_input": True},
    )
    language: str = Field(
        default="multi",
        description="Language code. 'multi' enables Nova-3 auto-detect.",
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
