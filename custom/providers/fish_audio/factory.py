"""Create Pipecat FishAudioTTSService from a stored VoiceEU TTS config."""

from fastapi import HTTPException
from pipecat.services.fish.tts import FishAudioTTSService, FishAudioTTSSettings
from pipecat.transcriptions.language import Language
from pipecat.utils.text.xml_function_tag_filter import XMLFunctionTagFilter

from custom.providers.fish_audio.config import LATENCY_MODES


def create_fish_audio_tts(user_config, audio_config):
    voice = getattr(user_config.tts, "voice", None)
    if not voice:
        raise HTTPException(
            status_code=400,
            detail=(
                "Fish Audio TTS requires a voice (reference_id). "
                "Configure it in your TTS settings."
            ),
        )
    model = getattr(user_config.tts, "model", None) or "s2-pro"
    language_code = getattr(user_config.tts, "language", None) or "en"
    latency = getattr(user_config.tts, "latency", None) or "balanced"
    if latency not in LATENCY_MODES:
        latency = "balanced"
    speed = getattr(user_config.tts, "speed", None)
    volume = getattr(user_config.tts, "volume", None)
    normalize = getattr(user_config.tts, "normalize", True)
    try:
        pipecat_language = Language(language_code)
    except ValueError:
        pipecat_language = language_code
    settings_kwargs = {
        "model": model,
        "voice": voice,
        "language": pipecat_language,
        "latency": latency,
        "normalize": True if normalize is None else normalize,
    }
    if speed is not None:
        settings_kwargs["prosody_speed"] = speed
    if volume is not None:
        settings_kwargs["prosody_volume"] = volume
    return FishAudioTTSService(
        api_key=user_config.tts.api_key,
        sample_rate=audio_config.transport_out_sample_rate,
        output_format="pcm",
        settings=FishAudioTTSSettings(**settings_kwargs),
        text_filters=[XMLFunctionTagFilter()],
        skip_aggregator_types=["recording_router", "recording"],
        silence_time_s=1.0,
    )
