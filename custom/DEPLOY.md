# Deploy VoiceEU + Guardian

One checkout. One command. Dograh and Guardian start together.

## First time on a VPS

```bash
git clone -b Guardian-Dograh https://github.com/dsactivi-2/dograhfork.git
cd dograhfork
git remote add upstream https://github.com/dograh-hq/dograh.git
sudo ./setup_remote.sh          # writes .env (PUBLIC_HOST, secrets)
bash custom/scripts/deploy.sh remote
```

Open:

| What | Where |
| --- | --- |
| Dograh (calls, workflows) | `https://YOUR_HOST` |
| Guardian (watch + overlay) | `http://YOUR_HOST:8787` |

Firewall: open **8787/tcp** for Guardian (Dograh itself uses 80/443).

Optional: set `GUARDIAN_TOKEN` in `.env` so Guardian is not public.

## First time on your laptop

```bash
git clone -b Guardian-Dograh https://github.com/dsactivi-2/dograhfork.git
cd dograhfork
bash custom/scripts/deploy.sh
```

- Dograh: http://localhost:3010
- Guardian: http://localhost:8787

## After it is up

1. Open Dograh → create / open a workflow.
2. STT and TTS pickers must list **Deepgram** and **Deepgram EU**.
3. Choose **Deepgram EU** when audio must stay on `api.eu.deepgram.com`.
4. Open Guardian. Dograh health must be green. Sweep must pass.

## Update official Dograh later

```bash
./custom/guardian/update.sh
./custom/scripts/deploy.sh remote    # or local
```

`custom/` is merge-protected. If a seam (`CUSTOM-SEAM`) is lost, deploy stops.

## What must never happen

- Do not edit the official Deepgram provider to change its URL.
- Do not run plain `docker compose up` — that pulls the stock image without `custom/`.
- Always use `./custom/scripts/deploy.sh` so the overlay compose file is loaded.
