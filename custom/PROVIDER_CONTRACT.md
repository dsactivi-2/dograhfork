# Provider contract

A custom provider is valid only if all of these are true.

1. `PROVIDER_ID` is **not** an upstream id (`deepgram`, `elevenlabs`, …).
2. Schema class uses `Literal[ServiceProviders.<NEW>]` and `@register_stt` / `@register_tts`.
3. Factory lives in `custom/providers/<id>/factory.py`.
4. Validator talks to the correct host and names that host in errors.
5. Seams are the four core files plus any new `elif` / enum / union line, each marked `CUSTOM-SEAM`.
6. US Deepgram still has no `base_url` field.
