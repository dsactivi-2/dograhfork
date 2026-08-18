"""Runtime factory for Deepgram EU. Mirrors US Deepgram plus official EU hosts."""

from api.services.configuration.options import DEEPGRAM_FLUX_MODELS
from custom.providers.deepgram_eu.config import (
    FLUX_LISTEN_URL,
    HTTP_BASE_URL,
    WS_BASE_URL,
)
from pipecat.services.deepgram.flux.stt import (
    DeepgramFluxSTTService,
    DeepgramFluxSTTSettings,
)
from pipecat.services.deepgram.stt import DeepgramSTTService, DeepgramSTTSettings
from pipecat.services.deepgram.tts import DeepgramTTSService, DeepgramTTSSettings
from pipecat.transcriptions.language import Language
from pipecat.utils.text.xml_function_tag_filter import XMLFunctionTagFilter

# Copied from the US factory so this module never imports service_factory
# (that import is a cycle: factory seam → this file).
_FLUX_LANGUAGE_HINTS = {
    "de": Language.DE,
    "en": Language.EN,
    "es": Language.ES,
    "fr": Language.FR,
    "hi": Language.HI,
    "it": Language.IT,
    "ja": Language.JA,
    "nl": Language.NL,
    "pt": Language.PT,
    "ru": Language.RU,
}


def deepgram_eu_uses_external_turns(user_config) -> bool:
    return user_config.stt.model in DEEPGRAM_FLUX_MODELS


def create_deepgram_eu_stt(user_config, audio_config, keyterms=None):
    if user_config.stt.model in DEEPGRAM_FLUX_MODELS:
        settings_kwargs = {
            "model": user_config.stt.model,
            "eot_timeout_ms": 3000,
            "eot_threshold": 0.7,
            "eager_eot_threshold": 0.5,
            "keyterm": keyterms or [],
        }
        if user_config.stt.model == "flux-general-multi":
            language = getattr(user_config.stt, "language", None)
            language_hint = _FLUX_LANGUAGE_HINTS.get(language)
            if language_hint:
                settings_kwargs["language_hints"] = [language_hint]

        return DeepgramFluxSTTService(
            api_key=user_config.stt.api_key,
            url=FLUX_LISTEN_URL,
            settings=DeepgramFluxSTTSettings(**settings_kwargs),
            should_interrupt=False,
            sample_rate=audio_config.transport_in_sample_rate,
        )

    language = getattr(user_config.stt, "language", None) or "multi"
    return DeepgramSTTService(
        api_key=user_config.stt.api_key,
        base_url=HTTP_BASE_URL,
        settings=DeepgramSTTSettings(
            language=language,
            profanity_filter=False,
            endpointing=100,
            model=user_config.stt.model,
            keyterm=keyterms or [],
        ),
        should_interrupt=False,
        sample_rate=audio_config.transport_in_sample_rate,
    )


def create_deepgram_eu_tts(user_config, audio_config):
    xml_function_tag_filter = XMLFunctionTagFilter()
    return DeepgramTTSService(
        api_key=user_config.tts.api_key,
        base_url=WS_BASE_URL,
        settings=DeepgramTTSSettings(voice=user_config.tts.voice),
        text_filters=[xml_function_tag_filter],
        skip_aggregator_types=["recording_router", "recording"],
        silence_time_s=1.0,
    )
