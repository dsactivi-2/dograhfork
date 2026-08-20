from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from custom.processors.emotion_text_filter import EmotionTextFilter
from custom.providers.fish_audio.factory import create_fish_audio_tts
from custom.providers.fish_audio.validate import check_fish_audio_api_key
from pipecat.utils.text.xml_function_tag_filter import XMLFunctionTagFilter


def _audio():
    return SimpleNamespace(transport_out_sample_rate=16000)


def test_create_fish_audio_requires_voice():
    user = SimpleNamespace(
        tts=SimpleNamespace(
            provider="fish_audio",
            api_key="k",
            model="s2-pro",
            voice=None,
        )
    )
    with pytest.raises(HTTPException):
        create_fish_audio_tts(user, _audio())


def test_create_fish_audio_uses_pcm_and_settings():
    user = SimpleNamespace(
        tts=SimpleNamespace(
            provider="fish_audio",
            api_key="k",
            model="s2.1-pro",
            voice="abc123voice",
            language="bs",
            latency="balanced",
            speed=1.1,
            volume=2,
            normalize=True,
            temperature=0.65,
            top_p=0.8,
        )
    )
    with patch("custom.providers.fish_audio.factory.FishAudioTTSService") as mocked:
        create_fish_audio_tts(user, _audio())
        kwargs = mocked.call_args.kwargs
        assert kwargs["output_format"] == "pcm"
        assert kwargs["sample_rate"] == 16000
        settings = kwargs["settings"]
        assert settings.voice == "abc123voice"
        assert settings.model == "s2.1-pro"
        assert settings.temperature == 0.65
        assert settings.top_p == 0.8
        filters = kwargs["text_filters"]
        assert len(filters) == 2
        assert isinstance(filters[0], XMLFunctionTagFilter)
        assert isinstance(filters[1], EmotionTextFilter)
        assert filters[1].default_tag == "friendly"
        assert filters[1].enabled is True


def test_create_fish_audio_honors_emotion_overrides():
    user = SimpleNamespace(
        tts=SimpleNamespace(
            provider="fish_audio",
            api_key="k",
            model="s2.1-pro",
            voice="abc123voice",
            language="bs",
            latency="balanced",
            speed=1.0,
            volume=0,
            normalize=True,
            emotion_default_tag="empathetic",
            emotion_inject=False,
        )
    )
    with patch("custom.providers.fish_audio.factory.FishAudioTTSService") as mocked:
        create_fish_audio_tts(user, _audio())
        filters = mocked.call_args.kwargs["text_filters"]
        assert isinstance(filters[1], EmotionTextFilter)
        assert filters[1].default_tag == "empathetic"
        assert filters[1].enabled is False


def test_fish_audio_key_validation_accepts_ok(monkeypatch):
    class _Resp:
        status_code = 200

    monkeypatch.setattr(
        "custom.providers.fish_audio.validate.httpx.get",
        lambda *a, **k: _Resp(),
    )
    assert check_fish_audio_api_key("good") is True


def test_fish_audio_key_validation_rejects_401(monkeypatch):
    class _Resp:
        status_code = 401

    monkeypatch.setattr(
        "custom.providers.fish_audio.validate.httpx.get",
        lambda *a, **k: _Resp(),
    )
    with pytest.raises(ValueError, match="api.fish.audio"):
        check_fish_audio_api_key("bad")
