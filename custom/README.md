# VoiceEU custom overlay

This directory is the **only** place permanent Dograh customizations live.

| Module | What it adds |
| --- | --- |
| `providers/deepgram_eu/` | New STT/TTS provider `deepgram_eu` → `api.eu.deepgram.com` |
| `providers/fish_audio/` | New TTS provider `fish_audio` (Pipecat `FishAudioTTSService`) |
| `branding/` | Docs name + banner + support URL |
| `guardian/` | Healthcheck, branding apply, safe upstream merge |

Upstream Deepgram (`provider: "deepgram"`) is **byte-identical** to official Dograh.
Never add a `base_url` field to it.

After every `git merge upstream/main`:

```bash
python3 custom/guardian/apply_branding.py
python3 custom/guardian/healthcheck.py
```
