PROVIDER_ID = "deepgram_3"
PROVIDER_TITLE = "Deepgram 3"
DOCS_URL = "https://developers.deepgram.com/docs/understand-endpointing-interim-results"

# Nova-3 live-agent defaults used by VoiceEU agents.
# No keyterms, no utterance_end_ms. interim_results off.
STT_DEFAULTS = {
    "endpointing": 400,
    "smart_format": True,
    "punctuate": True,
    "numerals": True,
    "interim_results": False,
    "diarize": False,
    "vad_events": True,
}
