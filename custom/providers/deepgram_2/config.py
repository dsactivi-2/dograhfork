from custom.providers.deepgram_common import LIVE_STT_DEFAULTS

PROVIDER_ID = "deepgram_2"
PROVIDER_TITLE = "Deepgram 2"
DOCS_URL = "https://developers.deepgram.com/docs/understand-endpointing-interim-results"

# Shared live-agent extras on top of upstream Deepgram. Official US Deepgram is unchanged.
STT_DEFAULTS = dict(LIVE_STT_DEFAULTS)
