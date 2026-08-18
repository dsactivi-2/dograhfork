"""Import-time registration of every VoiceEU overlay provider.

Called from the registry.py CUSTOM-SEAM. Importing schema modules runs
@register_stt / @register_tts and fills REGISTRY.
"""


def register_all() -> None:
    from custom.providers.deepgram_eu import schema as _deepgram_eu_schema
    from custom.providers.fish_audio import schema as _fish_audio_schema

    _ = (_deepgram_eu_schema, _fish_audio_schema)
