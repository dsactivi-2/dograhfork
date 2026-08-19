from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from custom.providers.fish_audio.factory import create_fish_audio_tts
from custom.providers.fish_audio.validate import check_fish_audio_api_key


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
        )
    )
    with patch("custom.providers.fish_audio.factory.FishAudioTTSService") as mocked:
        create_fish_audio_tts(user, _audio())
        kwargs = mocked.call_args.kwargs
        assert kwargs["output_format"] == "pcm"
        assert kwargs["sample_rate"] == 16000
        assert kwargs["settings"].voice == "abc123voice"
        assert kwargs["settings"].model == "s2.1-pro"


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
