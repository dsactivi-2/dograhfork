PROVIDER_ID = "deepgram_2"
PROVIDER_TITLE = "Deepgram 2"
DOCS_URL = "https://developers.deepgram.com/docs/understand-endpointing-interim-results"

# Live-agent extras on top of upstream Deepgram.
STT_DEFAULTS = {
    "interim_results": True,
    "smart_format": True,
    "punctuate": True,
    "endpointing": 100,
}
