from types import SimpleNamespace
from unittest.mock import patch

from custom.providers.deepgram_2.factory import create_deepgram_2_stt
from custom.providers.deepgram_3.factory import create_deepgram_3_stt
from custom.providers.deepgram_common import deepgram_inference_urls, live_stt_settings_kwargs


def _audio():
    return SimpleNamespace(transport_in_sample_rate=16000)


def _user(provider, model="nova-3-general", **stt_overrides):
    stt = {
        "provider": provider,
        "model": model,
        "language": "multi",
        "api_key": "k",
    }
    stt.update(stt_overrides)
    return SimpleNamespace(stt=SimpleNamespace(**stt))


def _assert_shared_live_flags(settings, *, keyterms=None):
    assert settings.smart_format is True
    assert settings.interim_results is False
    assert settings.endpointing == 100
    assert settings.diarize is True
    assert settings.punctuate is True
    assert settings.profanity_filter is False
    assert settings.keyterm == (keyterms or [])
    assert settings.extra.get("redact") is False
    assert settings.extra.get("replace") is True


def test_urls_default_eu(monkeypatch):
    monkeypatch.delenv("DEEPGRAM_BASE_URL", raising=False)
    urls = deepgram_inference_urls()
    assert urls["host"] == "api.eu.deepgram.com"
    assert urls["flux_listen"] == "wss://api.eu.deepgram.com/v2/listen"


def test_urls_follow_env(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_BASE_URL", "https://api.eu.deepgram.com")
    urls = deepgram_inference_urls()
    assert urls["host"] == "api.eu.deepgram.com"
    assert urls["flux_listen"] == "wss://api.eu.deepgram.com/v2/listen"


def test_deepgram_2_sets_live_flags():
    with patch("custom.providers.deepgram_2.factory.DeepgramSTTService") as mocked:
        create_deepgram_2_stt(_user("deepgram_2"), _audio(), keyterms=["acme"])
        settings = mocked.call_args.kwargs["settings"]
        _assert_shared_live_flags(settings, keyterms=["acme"])


def test_deepgram_3_keeps_keyterms_and_live_flags():
    with patch("custom.providers.deepgram_3.factory.DeepgramSTTService") as mocked:
        create_deepgram_3_stt(_user("deepgram_3"), _audio(), keyterms=["keep-me"])
        settings = mocked.call_args.kwargs["settings"]
        _assert_shared_live_flags(settings, keyterms=["keep-me"])
        assert settings.numerals is True
        assert settings.extra.get("vad_events") is True


def test_live_settings_honor_user_overrides():
    user = _user(
        "deepgram_2",
        interim_results=True,
        diarize=False,
        endpointing=False,
        keyterm_prompting=False,
        redact=True,
        replace=False,
    )
    kwargs = live_stt_settings_kwargs(
        user, model="nova-3-general", language="multi", keyterms=["skip"]
    )
    assert kwargs["interim_results"] is True
    assert kwargs["diarize"] is False
    assert kwargs["endpointing"] is False
    assert kwargs["keyterm"] == []
    assert kwargs["extra"]["redact"] is True
    assert kwargs["extra"]["replace"] is False


def test_deepgram_3_flux_uses_listen_url(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_BASE_URL", "https://api.eu.deepgram.com")
    with patch("custom.providers.deepgram_3.factory.DeepgramFluxSTTService") as mocked:
        create_deepgram_3_stt(_user("deepgram_3", "flux-general-en"), _audio(), keyterms=["flux"])
        assert mocked.call_args.kwargs["url"] == "wss://api.eu.deepgram.com/v2/listen"
        assert mocked.call_args.kwargs["settings"].keyterm == ["flux"]
