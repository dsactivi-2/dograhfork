"""API-key check against the Deepgram EU host, not api.deepgram.com."""

from deepgram import DeepgramClient
from deepgram.environment import DeepgramEnvironment

from custom.providers.deepgram_eu.config import STT_HOST


def check_deepgram_eu_api_key(api_key: str) -> bool:
    try:
        # Prefer explicit environment when the installed SDK exposes it.
        try:
            client = DeepgramClient(
                api_key=api_key,
                environment=DeepgramEnvironment(STT_HOST),
            )
        except (TypeError, ValueError, AttributeError):
            client = DeepgramClient(api_key=api_key)
        client.manage.v1.projects.list()
        return True
    except Exception as exc:
        raise ValueError(
            "Invalid Deepgram API key for the EU endpoint "
            f"({STT_HOST}). The key was rejected by Deepgram EU. "
            "Please check that your API key is correct and active. "
            "You can verify your keys at https://console.deepgram.com/. "
            f"Detail: {exc}"
        ) from exc
