---
name: voiceeu-guardian
description: >
  Bind to the VoiceEU Guardian next to Dograh. Use for overlay config, change
  history after deploys, provider map, seams, and the typical Fish+Deepgram
  agent. Never edit official Deepgram. Never rewrite custom/.
---

# VoiceEU Guardian

You are talking to a **Dograh fork with a sealed overlay**, not vanilla Dograh.

## Connect (MCP)

```
POST http://<host>:8787/mcp
Authorization: Bearer <GUARDIAN_TOKEN>   # if set
Content-Type: application/json
```

Discovery: `GET http://<host>:8787/.well-known/mcp.json`

Initialize with protocol `2024-11-05`, then `tools/list` / `tools/call`.

REST (same data, no MCP client needed):

| Method | Path | Why |
| --- | --- | --- |
| GET | `/api/status` | Dograh + overlay pulse |
| GET | `/api/config` | Live config (secrets redacted unless `?raw=1`) |
| PUT | `/api/config` | Save config — writes history + `runtime.env` |
| GET | `/api/history` | What changed when (deploy diffs included) |
| GET | `/api/contract` | Paths, seams, factory locks |
| GET | `/api/combo` | Typical agent JSON |
| GET | `/api/skill` | This file |
| GET | `/api/checks` | Seam healthcheck |

## First calls after bind

1. `guardian_contract` — where files live, what is forbidden
2. `guardian_status` — is Dograh up, is overlay present
3. `guardian_history` — did the last deploy overwrite something
4. `guardian_config_get` — current VoiceEU defaults
5. `guardian_agent_combo` — JSON to put on an agent

## What you may change

- Overlay config via `guardian_config_set` (Deepgram EU host, Fish defaults, integration URLs)
- Notes in config
- Never: `api/services/configuration/options/deepgram.py`
- Never: collapse `deepgram_eu` / `deepgram_2` / `deepgram_3` / `fish_audio` into official ids
- Never: unattended rewrite of `custom/`
- Seams (`CUSTOM-SEAM`) only if a human is merging upstream and a marker vanished

## Typical agent

STT `deepgram_3` + TTS `fish_audio`. Fish **requires** `voice` (reference_id).  
Setup: `custom/FISH_VOICE.md`. Factory locks: `custom/CONFIG.md`.

## If a deploy overwrote something

`guardian_history` → events `deploy.diff` list `added` / `changed` / `removed`.  
Those paths are what the last boot saw differ from the previous snapshot.  
Config itself lives in `custom/guardian/state/` (volume) and is **not** reset by `docker compose up --build`.
