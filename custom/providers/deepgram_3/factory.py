"""Build Deepgram 3 STT. Does not import service_factory (cycle)."""

from custom.providers.deepgram_3.config import STT_DEFAULTS
from custom.providers.deepgram_common import deepgram_inference_urls, is_flux_model
from custom.providers.deepgram_eu.factory import _FLUX_LANGUAGE_HINTS
from pipecat.services.deepgram.flux.stt import DeepgramFluxSTTService, DeepgramFluxSTTSettings
from pipecat.services.deepgram.stt import DeepgramSTTService, DeepgramSTTSettings


def deepgram_3_uses_external_turns(user_config) -> bool:
    return is_flux_model(getattr(user_config.stt, "model", None))


def create_deepgram_3_stt(user_config, audio_config, keyterms=None):
    del keyterms  # Nova-3 live profile: no keyterms
    urls = deepgram_inference_urls()
    model = user_config.stt.model
    if is_flux_model(model):
        settings_kwargs = {
            "model": model,
            "eot_timeout_ms": 3000,
            "eot_threshold": 0.7,
            "eager_eot_threshold": 0.5,
        }
        if model == "flux-general-multi":
            language = getattr(user_config.stt, "language", None)
            hint = _FLUX_LANGUAGE_HINTS.get(language)
            if hint:
                settings_kwargs["language_hints"] = [hint]
        return DeepgramFluxSTTService(
            api_key=user_config.stt.api_key,
            url=urls["flux_listen"],
            settings=DeepgramFluxSTTSettings(**settings_kwargs),
            should_interrupt=False,
            sample_rate=audio_config.transport_in_sample_rate,
        )

    language = getattr(user_config.stt, "language", None) or "multi"
    return DeepgramSTTService(
        api_key=user_config.stt.api_key,
        base_url=urls["stt_host"],
        settings=DeepgramSTTSettings(
            language=language,
            profanity_filter=False,
            endpointing=STT_DEFAULTS["endpointing"],
            model=model,
            smart_format=STT_DEFAULTS["smart_format"],
            punctuate=STT_DEFAULTS["punctuate"],
            numerals=STT_DEFAULTS["numerals"],
            interim_results=STT_DEFAULTS["interim_results"],
            diarize=STT_DEFAULTS["diarize"],
            extra={"vad_events": STT_DEFAULTS["vad_events"]},
        ),
        should_interrupt=False,
        sample_rate=audio_config.transport_in_sample_rate,
    )
