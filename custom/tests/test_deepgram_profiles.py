from types import SimpleNamespace
from unittest.mock import patch

from custom.providers.deepgram_2.factory import create_deepgram_2_stt
from custom.providers.deepgram_3.factory import create_deepgram_3_stt
from custom.providers.deepgram_common import deepgram_inference_urls


def _audio():
    return SimpleNamespace(transport_in_sample_rate=16000)


def _user(provider, model="nova-3-general"):
    return SimpleNamespace(
        stt=SimpleNamespace(
            provider=provider,
            model=model,
            language="multi",
            api_key="k",
        )
    )


def test_urls_default_us(monkeypatch):
    monkeypatch.delenv("DEEPGRAM_BASE_URL", raising=False)
    urls = deepgram_inference_urls()
    assert urls["host"] == "api.deepgram.com"
    assert urls["flux_listen"] == "wss://api.deepgram.com/v2/listen"


def test_urls_follow_env(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_BASE_URL", "https://api.eu.deepgram.com")
    urls = deepgram_inference_urls()
    assert urls["host"] == "api.eu.deepgram.com"
    assert urls["flux_listen"] == "wss://api.eu.deepgram.com/v2/listen"


def test_deepgram_2_sets_live_flags():
    with patch("custom.providers.deepgram_2.factory.DeepgramSTTService") as mocked:
        create_deepgram_2_stt(_user("deepgram_2"), _audio())
        settings = mocked.call_args.kwargs["settings"]
        assert settings.interim_results is True
        assert settings.smart_format is True
        assert settings.punctuate is True


def test_deepgram_3_nova_defaults_no_keyterms():
    with patch("custom.providers.deepgram_3.factory.DeepgramSTTService") as mocked:
        create_deepgram_3_stt(_user("deepgram_3"), _audio(), keyterms=["ignore-me"])
        kwargs = mocked.call_args.kwargs
        settings = kwargs["settings"]
        assert settings.endpointing == 400
        assert settings.extra.get("vad_events") is True
        assert not getattr(settings, "keyterm", None)


def test_deepgram_3_flux_uses_listen_url(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_BASE_URL", "https://api.eu.deepgram.com")
    with patch("custom.providers.deepgram_3.factory.DeepgramFluxSTTService") as mocked:
        create_deepgram_3_stt(_user("deepgram_3", "flux-general-en"), _audio())
        assert mocked.call_args.kwargs["url"] == "wss://api.eu.deepgram.com/v2/listen"
