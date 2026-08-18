"""API-key check against api.eu.deepgram.com (not the US host)."""

from deepgram import DeepgramClient

from custom.providers.deepgram_eu.config import STT_HOST, build_eu_environment


def check_deepgram_eu_api_key(api_key: str) -> bool:
    try:
        try:
            client = DeepgramClient(api_key=api_key, environment=build_eu_environment())
        except TypeError:
            # Very old SDK without environment= — last resort, error still names EU host.
            client = DeepgramClient(api_key=api_key)
        client.manage.v1.projects.list()
        return True
    except Exception as exc:
        raise ValueError(
            "Invalid Deepgram API key for the EU endpoint "
            f"({STT_HOST}). Existing US keys work on EU — no extra activation. "
            "If this fails, the key is wrong or Deepgram rejected the request. "
            "Verify at https://console.deepgram.com/. "
            f"Detail: {exc}"
        ) from exc
