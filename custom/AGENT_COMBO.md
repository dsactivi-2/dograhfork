# Typical VoiceEU agent

Full two-layer config (UI vs factory): [CONFIG.md](./CONFIG.md).

```json
{
  "stt": {
    "provider": "deepgram_3",
    "api_key": "DEIN_DEEPGRAM_KEY",
    "model": "nova-3-general",
    "language": "multi"
  },
  "tts": {
    "provider": "fish_audio",
    "api_key": "DEIN_FISH_KEY",
    "model": "s2.1-pro",
    "voice": "<fish-reference-id>",
    "language": "de",
    "latency": "balanced"
  }
}
```

| STT | Wann |
| --- | --- |
| `deepgram` | Bestehende Agenten, Official-Defaults |
| `deepgram_2` | Mehr Live-Interim / smart_format |
| `deepgram_3` | Nova-3 Live (VoiceEU Standard) |
| `deepgram_eu` | Expliziter EU-Host, Official-Settings |

`deepgram_2` / `deepgram_3` defaulten Inference auf `api.eu.deepgram.com`.
Override: `DEEPGRAM_BASE_URL`. Key-Check bleibt US.
Ohne Fish-Voice → Factory 400.
