# VoiceEU custom overlay

This directory is the **only** place permanent Dograh customizations live.

| Module | What it adds |
| --- | --- |
| `providers/deepgram_eu/` | New STT/TTS provider `deepgram_eu` → `api.eu.deepgram.com` |
| `providers/deepgram_2/` | Live-agent STT: interim + smart_format + punctuate |
| `providers/deepgram_3/` | Nova-3 live defaults (endpointing=400, vad_events) |
| `providers/fish_audio/` | New TTS provider `fish_audio` |
| `branding/` | Docs name + banner + support URL |
| `guardian/` | CLI healthcheck + branding apply + safe merge |
| `guardian/web/` | Live Guardian next to Dograh (port 8787) |
| `compose.overlay.yaml` | Additive compose: rebuild API with overlay + start Guardian |
| `scripts/deploy.sh` | The only start command you need |

Upstream Deepgram (`provider: "deepgram"`) stays byte-identical.
Never add a `base_url` field to it.

## Start

```bash
bash custom/scripts/deploy.sh          # laptop
bash custom/scripts/deploy.sh remote   # VPS after setup_remote.sh
bash custom/scripts/diagnose.sh        # if something is red
```

See [DEPLOY.md](./DEPLOY.md) (includes Fehlerbehebung).
See [CONFIG.md](./CONFIG.md) for UI vs factory settings.

## After every upstream merge

```bash
python3 custom/guardian/apply_branding.py
python3 custom/guardian/healthcheck.py
./custom/scripts/deploy.sh remote
```
