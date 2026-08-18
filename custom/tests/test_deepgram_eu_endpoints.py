from custom.providers.deepgram_eu.config import (
    FLUX_LISTEN_URL,
    HTTP_BASE_URL,
    LISTEN_V1_URL,
    PROVIDER_ID,
    STT_HOST,
    TTS_SPEAK_URL,
    WS_BASE_URL,
)


def test_official_eu_hosts():
    assert PROVIDER_ID == "deepgram_eu"
    assert STT_HOST == "api.eu.deepgram.com"
    assert HTTP_BASE_URL == "https://api.eu.deepgram.com"
    assert WS_BASE_URL == "wss://api.eu.deepgram.com"
    assert LISTEN_V1_URL == "wss://api.eu.deepgram.com/v1/listen"
    assert FLUX_LISTEN_URL == "wss://api.eu.deepgram.com/v2/listen"
    assert TTS_SPEAK_URL == "wss://api.eu.deepgram.com/v1/speak"
    assert "api.deepgram.com" not in HTTP_BASE_URL.replace("api.eu.deepgram.com", "")
    assert STT_HOST != "api.deepgram.com"
