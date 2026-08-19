from types import SimpleNamespace
from unittest.mock import patch

from custom.providers.deepgram_eu.factory import (
    create_deepgram_eu_stt,
    create_deepgram_eu_tts,
)


def _audio():
    return SimpleNamespace(transport_in_sample_rate=16000, transport_out_sample_rate=16000)


def test_eu_stt_passes_eu_host():
    user = SimpleNamespace(
        stt=SimpleNamespace(
            provider="deepgram_eu",
            model="nova-3-general",
            language="de",
            api_key="k",
        )
    )
    with patch(
        "custom.providers.deepgram_eu.factory.DeepgramSTTService"
    ) as mocked:
        create_deepgram_eu_stt(user, _audio())
        kwargs = mocked.call_args.kwargs
        assert "api.eu.deepgram.com" in kwargs["base_url"]


def test_eu_flux_passes_eu_listen_url():
    user = SimpleNamespace(
        stt=SimpleNamespace(
            provider="deepgram_eu",
            model="flux-general-en",
            language="en",
            api_key="k",
        )
    )
    with patch(
        "custom.providers.deepgram_eu.factory.DeepgramFluxSTTService"
    ) as mocked:
        create_deepgram_eu_stt(user, _audio())
        assert mocked.call_args.kwargs["url"] == "wss://api.eu.deepgram.com/v2/listen"


def test_eu_tts_passes_eu_ws_host():
    user = SimpleNamespace(
        tts=SimpleNamespace(provider="deepgram_eu", voice="aura-2-helena-en", api_key="k")
    )
    with patch(
        "custom.providers.deepgram_eu.factory.DeepgramTTSService"
    ) as mocked:
        create_deepgram_eu_tts(user, _audio())
        assert "api.eu.deepgram.com" in mocked.call_args.kwargs["base_url"]
