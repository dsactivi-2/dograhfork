PROVIDER_ID = "deepgram_3"
PROVIDER_TITLE = "Deepgram 3"
DOCS_URL = "https://developers.deepgram.com/docs/understand-endpointing-interim-results"

# Nova-3 live-agent defaults used by VoiceEU agents.
# No keyterms, no utterance_end_ms.
STT_DEFAULTS = {
    "endpointing": 400,
    "vad_events": True,
    "interim_results": True,
    "punctuate": True,
}
