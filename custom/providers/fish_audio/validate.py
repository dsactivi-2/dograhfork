"""Validate a Fish Audio API key against api.fish.audio."""

import httpx

from custom.providers.fish_audio.config import KEY_CHECK_URL


def check_fish_audio_api_key(api_key: str) -> bool:
    try:
        response = httpx.get(
            KEY_CHECK_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise ValueError(
            "Could not reach Fish Audio to validate the API key "
            f"({KEY_CHECK_URL}). Detail: {exc}"
        ) from exc
    if response.status_code == 200:
        return True
    if response.status_code in (401, 403):
        raise ValueError(
            "Invalid Fish Audio API key. The key was rejected by "
            f"{KEY_CHECK_URL}. Check the key at https://fish.audio/."
        )
    raise ValueError(
        f"Fish Audio key check failed with HTTP {response.status_code} "
        f"at {KEY_CHECK_URL}."
    )
