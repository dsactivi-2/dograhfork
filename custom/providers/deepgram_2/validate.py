from custom.providers.deepgram_common import check_deepgram_management_key


def check_deepgram_2_api_key(api_key: str) -> bool:
    return check_deepgram_management_key(api_key)
