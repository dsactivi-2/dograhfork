# Typical VoiceEU agent

Fish factory already enforces: voice required, `output_format=pcm`,
`sample_rate=transport_out_sample_rate`, model fallback `s2-pro`.
Set `model: s2.1-pro` in the agent JSON if you want the newer default
without waiting for upstream PR #37.

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
    "voice": "c737db0b875d4d0d88af86b7529e8fa1",
    "language": "de",
    "latency": "balanced",
    "speed": 1.0,
    "volume": 0,
    "normalize": true
  }
}
```

| STT picker | When |
| --- | --- |
| Deepgram | Existing agents, official defaults |
| Deepgram 2 | More live interim / smart_format |
| Deepgram 3 | Nova-3 live-agent defaults (usual VoiceEU) |
| Deepgram EU | Explicit EU host, official-like settings |

EU inference for Deepgram 2/3: set `DEEPGRAM_BASE_URL=https://api.eu.deepgram.com`
in `.env` (does **not** change official `deepgram`). Key check stays on US management.
