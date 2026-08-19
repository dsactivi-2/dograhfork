# VoiceEU Guardian

This branch (`Guardian-Dograh`) is Dograh **plus** the VoiceEU overlay.

- Overlay: [`custom/`](custom/)
- Deploy: [`custom/DEPLOY.md`](custom/DEPLOY.md)
- Config UI vs factory: [`custom/CONFIG.md`](custom/CONFIG.md)
- Fish voice-id: [`custom/FISH_VOICE.md`](custom/FISH_VOICE.md)

## One command

```bash
bash custom/scripts/deploy.sh          # laptop
bash custom/scripts/deploy.sh remote   # VPS
```

- Dograh: `:3010` / `https://HOST`
- Guardian: `:8787` — **Status, Config, History, MCP**

## Config + History

Set the overlay in Guardian (not by editing core). Every save writes:

- `custom/guardian/state/config.json`
- `custom/guardian/state/history.jsonl`
- `custom/guardian/state/runtime.env` (`DEEPGRAM_BASE_URL` → API)

That folder is a volume. `docker compose up --build` does **not** wipe it.

On Guardian boot a file snapshot is compared. If a deploy overwrote overlay/seam files, History shows `deploy.diff` with added/changed/removed paths.

## MCP (any agent)

```
POST http://HOST:8787/mcp
Authorization: Bearer $GUARDIAN_TOKEN
```

Discovery: `GET /.well-known/mcp.json`  
Client snippet: [`custom/guardian/mcp.json`](custom/guardian/mcp.json)  
Skill: [`custom/guardian/skills/voiceeu-guardian/SKILL.md`](custom/guardian/skills/voiceeu-guardian/SKILL.md)

Tools: `guardian_status`, `guardian_config_get/set`, `guardian_history`, `guardian_contract`, `guardian_agent_combo`, `guardian_skill`, `guardian_paths`, `guardian_diagnose`.
