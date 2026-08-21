from api.services.configuration.registry import REGISTRY, TTSConfig, ServiceType
from custom.providers.fish_audio.schema import FishAudioTTSConfiguration


def test_fish_audio_registered_for_tts_only():
    tts_keys = {getattr(k, "value", k) for k in REGISTRY[ServiceType.TTS]}
    stt_keys = {getattr(k, "value", k) for k in REGISTRY[ServiceType.STT]}
    assert "fish_audio" in tts_keys
    assert "fish_audio" not in stt_keys


def test_fish_audio_schema_title_and_defaults():
    schema = FishAudioTTSConfiguration.model_json_schema()
    assert schema["title"] == "Fish Audio"
    props = schema.get("properties") or {}
    assert "temperature" in props
    assert "top_p" in props
    parsed = TTSConfig.model_validate(
        {
            "provider": "fish_audio",
            "api_key": "k",
            "model": "s2-pro",
            "voice": "voice-1",
        }
    )
    assert parsed.latency == "balanced"
    assert parsed.language == "en"
    assert parsed.normalize is True
    assert parsed.temperature == 0.7
    assert parsed.top_p == 0.7


def test_fish_audio_schema_accepts_sampling_overrides():
    parsed = TTSConfig.model_validate(
        {
            "provider": "fish_audio",
            "api_key": "k",
            "model": "s2.1-pro",
            "voice": "voice-1",
            "temperature": 0.65,
            "top_p": 0.8,
        }
    )
    assert parsed.temperature == 0.65
    assert parsed.top_p == 0.8
