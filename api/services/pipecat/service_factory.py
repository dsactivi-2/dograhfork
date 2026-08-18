from functools import wraps
from typing import TYPE_CHECKING
from urllib.parse import urlencode, urlparse, urlunparse

import aiohttp
from fastapi import HTTPException
from loguru import logger

from api.constants import MPS_API_URL
from api.errors.failure import (
    ErrorSource,
    annotate_failure_metadata,
    classify_exception,
    log_failure,
)
from api.services.configuration.options import (
    DEEPGRAM_FLUX_MODELS,
    DEEPGRAM_FLUX_MULTILINGUAL_LANGUAGE_OPTIONS,
)
from api.services.configuration.registry import ServiceProviders
from api.services.pipecat.gemini_json_schema_adapter import (
    DograhGeminiJSONSchemaAdapter,
)
from api.services.pipecat.minimax_tts import MiniMaxOwnedSessionTTSService
from api.utils.url_security import validate_user_configured_service_url
from pipecat.services.assemblyai.stt import AssemblyAISTTService, AssemblyAISTTSettings
from pipecat.services.aws.llm import AWSBedrockLLMService, AWSBedrockLLMSettings
from pipecat.services.azure.llm import AzureLLMService, AzureLLMSettings
from pipecat.services.azure.stt import AzureSTTService, AzureSTTSettings
from pipecat.services.azure.tts import AzureTTSService, AzureTTSSettings
from pipecat.services.cartesia.stt import CartesiaSTTService, CartesiaSTTSettings
from pipecat.services.cartesia.tts import (
    CartesiaTTSService,
    CartesiaTTSSettings,
    GenerationConfig,
)
from pipecat.services.cartesia.turns.stt import CartesiaTurnsSTTService
from pipecat.services.deepgram.flux.stt import (
    DeepgramFluxSTTService,
    DeepgramFluxSTTSettings,
)
from pipecat.services.deepgram.stt import DeepgramSTTService, DeepgramSTTSettings
from pipecat.services.deepgram.tts import DeepgramTTSService, DeepgramTTSSettings
from pipecat.services.dograh.flux.stt import DograhFluxSTTService
from pipecat.services.dograh.llm import DograhLLMService
from pipecat.services.dograh.stt import DograhSTTService, DograhSTTSettings
from pipecat.services.dograh.tts import DograhTTSService, DograhTTSSettings
from pipecat.services.elevenlabs.stt import (
    CommitStrategy,
    ElevenLabsRealtimeSTTService,
    ElevenLabsRealtimeSTTSettings,
)
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService, ElevenLabsTTSSettings
from pipecat.services.gladia.stt import GladiaSTTService, GladiaSTTSettings
from pipecat.services.google.llm import GoogleLLMService, GoogleLLMSettings
from pipecat.services.google.stt import GoogleSTTService, GoogleSTTSettings
from pipecat.services.google.tts import GoogleTTSService, GoogleTTSSettings
from pipecat.services.google.vertex.llm import (
    GoogleVertexLLMService,
    GoogleVertexLLMSettings,
)
from pipecat.services.groq.llm import GroqLLMService, GroqLLMSettings
from pipecat.services.huggingface.llm import (
    HuggingFaceLLMService,
    HuggingFaceLLMSettings,
)
from pipecat.services.huggingface.stt import (
    HuggingFaceSTTService,
    HuggingFaceSTTSettings,
)
from pipecat.services.inworld.tts import InworldTTSService, InworldTTSSettings
from pipecat.services.lmnt.tts import LmntTTSService, LmntTTSSettings
from pipecat.services.minimax.llm import MiniMaxLLMService
from pipecat.services.minimax.tts import MiniMaxTTSSettings
from pipecat.services.openai._constants import OPENAI_SAMPLE_RATE
from pipecat.services.openai.base_llm import OpenAILLMSettings
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import (
    OpenAISTTService,
    OpenAISTTSettings,
)
from pipecat.services.openai.tts import OpenAITTSService, OpenAITTSSettings
from pipecat.services.openrouter.llm import OpenRouterLLMService, OpenRouterLLMSettings
from pipecat.services.rime.tts import RimeTTSService, RimeTTSSettings
from pipecat.services.sarvam.llm import SarvamLLMService, SarvamLLMSettings
from pipecat.services.sarvam.stt import SarvamSTTService, SarvamSTTSettings
from pipecat.services.sarvam.tts import SarvamTTSService, SarvamTTSSettings
from pipecat.services.smallest.stt import SmallestSTTService, SmallestSTTSettings
from pipecat.services.smallest.tts import SmallestTTSService, SmallestTTSSettings
from pipecat.services.speaches.llm import SpeachesLLMService, SpeachesLLMSettings
from pipecat.services.speaches.stt import SpeachesSTTService, SpeachesSTTSettings
from pipecat.services.speaches.tts import SpeachesTTSService, SpeachesTTSSettings
from pipecat.services.speechmatics.stt import (
    SpeechmaticsSTTService,
    SpeechmaticsSTTSettings,
)
from pipecat.services.xai.tts import XAITTSService, XAIWebsocketTTSSettings
from pipecat.transcriptions.language import Language
from pipecat.utils.text.xml_function_tag_filter import XMLFunctionTagFilter

if TYPE_CHECKING:
    from api.schemas.ai_model_configuration import EffectiveAIModelConfiguration
    from api.services.pipecat.audio_config import AudioConfig


def _report_service_factory_failures(
    source: ErrorSource,
    *,
    config_section: str | None = None,
    provider_argument: int | None = None,
):
    """Classify constructor failures and tag successful services for ErrorFrames."""

    def decorator(factory):
        @wraps(factory)
        def wrapped(*args, **kwargs):
            provider = None
            if config_section:
                user_config = args[0] if args else kwargs.get("user_config")
                config = getattr(user_config, config_section, None)
                provider = getattr(config, "provider", None)
            elif provider_argument is not None:
                if len(args) > provider_argument:
                    provider = args[provider_argument]
                else:
                    provider = kwargs.get("provider")

            provider_value = getattr(provider, "value", provider)
            error_owner = (
                "operator" if str(provider_value).lower() == "dograh" else "user"
            )
            try:
                service = factory(*args, **kwargs)
            except Exception as exc:
                log_failure(
                    classify_exception(
                        exc,
                        source=source,
                        provider=provider,
                        error_owner=error_owner,
                    )
                )
                raise

            return annotate_failure_metadata(
                service,
                source=source,
                provider=provider,
                error_owner=error_owner,
            )

        return wrapped

    return decorator


DEEPGRAM_FLUX_LANGUAGE_HINTS = {
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


def dograh_stt_uses_flux_language(language: str | None) -> bool:
    language = language or "multi"
    return language in DEEPGRAM_FLUX_MULTILINGUAL_LANGUAGE_OPTIONS


def _resolve_elevenlabs_stt_language(
    language_code: str | None,
) -> Language | str | None:
    if not language_code or language_code == "auto":
        return None
    try:
        return Language(language_code)
    except ValueError:
        return language_code


def _elevenlabs_websocket_url(base_url: str) -> str:
    """Normalize an ElevenLabs API base URL for WebSocket clients."""
    base_url = base_url.strip()
    parsed = urlparse(base_url)
    if not parsed.netloc:
        return base_url.rstrip("/")

    websocket_scheme = {
        "http": "ws",
        "https": "wss",
    }.get(parsed.scheme, parsed.scheme)
    return urlunparse(
        parsed._replace(
            scheme=websocket_scheme,
            path=parsed.path.rstrip("/"),
        )
    )


def _elevenlabs_realtime_stt_host(base_url: str) -> str:
    """Return the host/path prefix Pipecat's ElevenLabs realtime STT expects.

    Pipecat's realtime STT service builds
    ``wss://{host}/v1/speech-to-text/realtime`` internally, so remove the scheme
    from the same normalized WebSocket URL used by ElevenLabs TTS. Preserve
    netloc (including optional ports) and any path prefix used by BYOK proxies.
    """
    websocket_url = _elevenlabs_websocket_url(base_url)
    parsed = urlparse(websocket_url)
    if parsed.netloc:
        path = parsed.path
        return f"{parsed.netloc}{path}" if path else parsed.netloc
    return websocket_url


def stt_uses_external_turns(user_config) -> bool:
    if user_config.stt.provider in (
        ServiceProviders.DEEPGRAM.value,
        ServiceProviders.DEEPGRAM_2.value,
    ):
        return user_config.stt.model in DEEPGRAM_FLUX_MODELS
    if user_config.stt.provider == ServiceProviders.DOGRAH.value:
        return dograh_stt_uses_flux_language(getattr(user_config.stt, "language", None))
    if user_config.stt.provider == ServiceProviders.CARTESIA.value:
        return user_config.stt.model == "ink-2"
    return False


class DograhGoogleLLMService(GoogleLLMService):
    adapter_class = DograhGeminiJSONSchemaAdapter


class DograhGoogleVertexLLMService(GoogleVertexLLMService):
    adapter_class = DograhGeminiJSONSchemaAdapter


def _validate_runtime_service_url(url: str, field_name: str) -> None:
    try:
        validate_user_configured_service_url(
            url,
            field_name=field_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@_report_service_factory_failures(ErrorSource.STT, config_section="stt")
def create_stt_service(
    user_config,
    audio_config: "AudioConfig",
    keyterms: list[str] | None = None,
    correlation_id: str | None = None,
):
    """Create and return appropriate STT service based on user configuration

    Args:
        user_config: User configuration containing STT settings
        keyterms: Optional list of keyterms for speech recognition boosting (Deepgram only)
    """
    logger.info(
        f"Creating STT service: provider={user_config.stt.provider}, model={user_config.stt.model}"
    )
    if user_config.stt.provider == ServiceProviders.DEEPGRAM.value:
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
                language_hint = DEEPGRAM_FLUX_LANGUAGE_HINTS.get(language)
                if language_hint:
                    settings_kwargs["language_hints"] = [language_hint]

            return DeepgramFluxSTTService(
                api_key=user_config.stt.api_key,
                settings=DeepgramFluxSTTSettings(**settings_kwargs),
                should_interrupt=False,  # Let UserAggregator take care of sending InterruptionFrame
                sample_rate=audio_config.transport_in_sample_rate,
            )

        # Other models than flux
        # Use language from user config, defaulting to "multi" for multilingual support
        language = getattr(user_config.stt, "language", None) or "multi"
        return DeepgramSTTService(
            api_key=user_config.stt.api_key,
            settings=DeepgramSTTSettings(
                language=language,
                profanity_filter=False,
                endpointing=100,
                model=user_config.stt.model,
                keyterm=keyterms or [],
            ),
            should_interrupt=False,  # Let UserAggregator take care of sending InterruptionFrame
            sample_rate=audio_config.transport_in_sample_rate,
        )
    elif user_config.stt.provider == ServiceProviders.DEEPGRAM_2.value:
        # Deepgram 2: same models as Deepgram, pinned to EU endpoint
        eu_base_url = "wss://api.eu.deepgram.com"
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
                language_hint = DEEPGRAM_FLUX_LANGUAGE_HINTS.get(language)
                if language_hint:
                    settings_kwargs["language_hints"] = [language_hint]

            return DeepgramFluxSTTService(
                api_key=user_config.stt.api_key,
                base_url=eu_base_url,
                settings=DeepgramFluxSTTSettings(**settings_kwargs),
                should_interrupt=False,
                sample_rate=audio_config.transport_in_sample_rate,
            )

        language = getattr(user_config.stt, "language", None) or "multi"
        return DeepgramSTTService(
            api_key=user_config.stt.api_key,
            base_url=eu_base_url,
            settings=DeepgramSTTSettings(
                language=language,
                model=user_config.stt.model,
                smart_format=True,
                interim_results=False,
                endpointing=100,
                keyterm=keyterms or [],
                diarize=True,
                punctuate=True,
                profanity_filter=False,
            ),
            should_interrupt=False,
            sample_rate=audio_config.transport_in_sample_rate,
        )
    elif user_config.stt.provider == ServiceProviders.OPENAI.value:
        kwargs = {}
        base_url = getattr(user_config.stt, "base_url", None)
        if base_url:
            _validate_runtime_service_url(base_url, "base_url")
            kwargs["base_url"] = base_url
        return OpenAISTTService(
            api_key=user_config.stt.api_key,
            settings=OpenAISTTSettings(model=user_config.stt.model),
            should_interrupt=False,  # Let UserAggregator own interruption confirmation.
            **kwargs,
        )
    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid STT provider {user_config.stt.provider}"
        )
