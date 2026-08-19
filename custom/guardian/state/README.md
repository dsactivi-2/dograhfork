# Guardian state (survives deploys)

This folder is bind-mounted read-write into the Guardian container.

| File | Purpose |
| --- | --- |
| `config.json` | Live overlay config set in the Guardian UI / MCP |
| `history.jsonl` | Append-only: who changed what, when |
| `runtime.env` | Written from config — loaded by the API container |
| `snapshots/` | File hashes so a deploy overwrite is visible in History |

`config.json`, `history.jsonl`, `runtime.env` are gitignored.
They are the source of truth after first save.
