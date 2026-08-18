from custom.providers.deepgram_common import LIVE_STT_DEFAULTS

PROVIDER_ID = "deepgram_3"
PROVIDER_TITLE = "Deepgram 3"
DOCS_URL = "https://developers.deepgram.com/docs/understand-endpointing-interim-results"

# Same live-agent Listen flags as Deepgram 2, plus Nova-3 extras (numerals, VAD).
STT_DEFAULTS = {
    **LIVE_STT_DEFAULTS,
    "numerals": True,
    "vad_events": True,
}
