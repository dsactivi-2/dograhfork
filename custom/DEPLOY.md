# Deploy VoiceEU + Guardian

Ein Checkout. Ein Befehl. Dograh und Guardian starten zusammen.

## Erster Start auf dem VPS

```bash
git clone -b Guardian-Dograh https://github.com/dsactivi-2/dograhfork.git
cd dograhfork
git remote add upstream https://github.com/dograh-hq/dograh.git
git submodule update --init --recursive
sudo ./setup_remote.sh
bash custom/scripts/deploy.sh remote
```

`setup_remote.sh` muss mit `sudo` laufen. Es schreibt `.env` (PUBLIC_HOST, Secrets, Zertifikate).

Danach:

| Was | Adresse |
| --- | --- |
| Dograh (Anrufe, Workflows) | `https://DEINE-DOMAIN` oder `https://DEINE-IP` |
| Guardian (Config, History, MCP) | `http://DEINE-DOMAIN:8787` |

### Firewall

| Port | Wofür |
| --- | --- |
| TCP 80, 443 | Dograh UI + API |
| TCP 8787 | Guardian |
| TCP+UDP 3478, 5349 | TURN (WebRTC) |
| UDP 49152–49200 | Sprach-Audio |

Ohne die UDP-Ports: Anruf verbindet, **kein Ton**.

Optional in `.env`: `GUARDIAN_TOKEN=langes-geheimnis` — dann ist Guardian nicht öffentlich.

In Guardian unter **Config** die Overlay-Werte setzen (Deepgram-Host, Fish Voice, Defaults). Jede Änderung landet in **History**. MCP für Agents: `POST http://HOST:8787/mcp` — siehe [GUARDIAN.md](../GUARDIAN.md).

## Erster Start auf dem Laptop

```bash
git clone -b Guardian-Dograh https://github.com/dsactivi-2/dograhfork.git
cd dograhfork
git submodule update --init --recursive
bash custom/scripts/deploy.sh
```

- Dograh: http://localhost:3010
- Guardian: http://localhost:8787

## Nach dem Start prüfen

1. Dograh öffnen → Workflow anlegen.
2. STT und TTS müssen **Deepgram** und **Deepgram EU** zeigen.
3. Für EU-Audio **Deepgram EU** wählen.
4. Guardian öffnen: Dograh API grün, Sweep = pass.

```bash
bash custom/scripts/diagnose.sh
```

## Official Dograh später updaten

```bash
bash custom/guardian/update.sh
bash custom/scripts/deploy.sh remote
```

`custom/` ist merge-geschützt. Fehlt ein `CUSTOM-SEAM`, stoppt das Update.

## Niemals

- Offiziellen Deepgram-Provider umbauen (keine `base_url` dort).
- Nur `docker compose up` — das holt das Original-Image **ohne** Overlay.
- Immer `bash custom/scripts/deploy.sh` (lädt `custom/compose.overlay.yaml`).

---

# Fehlerbehebung

Zuerst Diagnose, dann den passenden Block unten.

```bash
cd ~/dograhfork   # oder wohin du geklont hast
bash custom/scripts/diagnose.sh
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml ps
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml logs --tail=80 api
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml logs --tail=80 guardian
```

Healthcheck-Codes:

| Exit | Bedeutung | Was tun |
| --- | --- | --- |
| 0 | Overlay + Nähte ok | Weiter, Stack prüfen |
| 2 | Datei in `custom/` fehlt | Branch `Guardian-Dograh`? `git status` |
| 3 | `CUSTOM-SEAM` in api/ verloren | Nicht „wegmergen“. Backup-Branch, Naht wieder einsetzen |
| 4 | Verbotene Änderung am US-Deepgram | `git checkout upstream/main -- api/services/configuration/options/deepgram.py` |

---

## 1. `custom/ overlay missing`

**Symptom:** `deploy.sh` endet mit „custom/ overlay missing“.

**Ursache:** Falscher Branch oder unvollständiger Clone.

```bash
git branch --show-current          # muss Guardian-Dograh sein
git checkout Guardian-Dograh
ls custom/providers/deepgram_eu/config.py
```

---

## 2. `Remote deploy needs PUBLIC_HOST`

**Symptom:** `deploy.sh remote` bricht ab.

**Ursache:** `setup_remote.sh` wurde nicht ausgeführt, oder `.env` ist leer.

```bash
sudo ./setup_remote.sh
grep '^PUBLIC_HOST=' .env
bash custom/scripts/deploy.sh remote
```

---

## 3. `OSS_JWT_SECRET must be set`

**Symptom:** API-Container startet nicht. Compose meckert über Secret.

```bash
grep OSS_JWT_SECRET .env
# wenn leer:
python3 -c 'import secrets; print("OSS_JWT_SECRET="+secrets.token_hex(32))' >> .env
bash custom/scripts/deploy.sh remote
```

---

## 4. `setup_remote.sh` bricht sofort ab

**Ursache:** Nicht als root.

```bash
sudo ./setup_remote.sh
```

Danach `.env` gehört oft `root`. Wenn später Speichern scheitert:

```bash
sudo chown -R "$USER:$USER" .
```

---

## 5. Guardian rot / Dograh API offline

**Warten:** Erster Start (Build) dauert mehrere Minuten.

Dann:

```bash
curl -sS http://127.0.0.1:8000/api/v1/health
curl -sS http://127.0.0.1:8787/api/health
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml ps
```

| Befund | Fix |
| --- | --- |
| API `unhealthy` / Restarting | `logs api` — oft Postgres-Passwort oder Secret |
| Port 8787 Connection refused | Guardian-Container down; `logs guardian` |
| Guardian im Browser nicht erreichbar | Firewall 8787/tcp öffnen |
| Guardian 401 | `GUARDIAN_TOKEN` steht in `.env` — gleichen Token mitsenden oder Zeile leeren und neu starten |

---

## 6. Kein Deepgram EU in der Dograh-UI

**Ursache:** Stock-Image ohne Overlay. Typisch nach bloßem `docker compose up` oder `remote_up.sh` ohne `deploy.sh`.

```bash
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml exec api \
  python -c "from api.services.configuration.registry import ServiceProviders; print(hasattr(ServiceProviders,'DEEPGRAM_EU'), getattr(ServiceProviders,'DEEPGRAM_EU',None))"
```

Muss `True deepgram_eu` sein. Sonst:

```bash
git submodule update --init --recursive
bash custom/scripts/deploy.sh remote
```

Prüfen, dass das Image lokal gebaut wurde:

```bash
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml images api
# Image-Name: dograh-guardian-api:local
```

Steht dort `dograhai/dograh-api:latest`, wurde das Overlay **nicht** geladen.

---

## 7. Anruf verbindet, aber kein Ton

**Ursache:** TURN/UDP zu. Nicht Guardian.

Firewall öffnen: UDP+TCP **3478**, **5349**, UDP **49152–49200**.

```bash
grep -E 'TURN_HOST|ENABLE_COTURN|PUBLIC_HOST' .env
```

`TURN_HOST` = öffentliche Server-IP. Browser-Konsole: `iceConnectionState: failed` = genau dieses Problem.

---

## 8. Browser warnt vor Zertifikat

Private IP → kein Let's Encrypt → selbstsigniert. Warnung einmal akzeptieren.

Oder Domain auf den Server zeigen und `setup_remote.sh` erneut.

---

## 9. `healthcheck` Exit 3 — Naht weg

Nach einem Upstream-Merge fehlt `CUSTOM-SEAM` in `registry.py` / `service_factory.py` / `check_validity.py` / `api/Dockerfile`.

```bash
rg -n "CUSTOM-SEAM" api/services/configuration/registry.py \
  api/services/pipecat/service_factory.py \
  api/services/configuration/check_validity.py \
  api/Dockerfile
```

Es müssen alle vier Dateien Treffer haben, inkl. `deepgram_eu`.

**Nicht** die Naht löschen, um den Merge „grün“ zu machen. Backup-Branch von `update.sh` nutzen und die markierten Zeilen wieder einsetzen. Karte: `custom/seams/SEAM_MAP.md`.

---

## 10. `healthcheck` Exit 4 — US-Deepgram angefasst

```bash
git diff upstream/main -- api/services/configuration/options/deepgram.py
git checkout upstream/main -- api/services/configuration/options/deepgram.py
```

EU gehört nur nach `custom/providers/deepgram_eu/`.

---

## 11. `dirty tree` bei `update.sh`

```bash
git status
git stash -u          # oder commit
bash custom/guardian/update.sh
```

---

## 12. Postgres will nicht (API crasht im Loop)

`POSTGRES_PASSWORD` in `.env` passt nicht zum alten Volume (Passwort gilt nur beim ersten Init).

```bash
# Diagnose
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml logs postgres | tail -40
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml logs api | tail -40
```

`remote_up.sh` / `deploy.sh remote` versucht, das Passwort zu synchronisieren. Wenn der Volume-Schrott bleibt und **keine Daten** drauf sind:

```bash
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml down
docker volume ls | grep postgres
# NUR auf leerem Test-Server:
# docker volume rm <project>_postgres_data
bash custom/scripts/deploy.sh remote
```

---

## 13. Build dauert ewig / bricht ab

Erster Build der API-Images: mehrere Minuten, braucht RAM.

```bash
free -h
df -h
git submodule update --init --recursive
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml build api
```

Mindestens ~8 GB RAM, ~4 vCPU empfohlen. Abbruch oft: Speicher, voller Disk, fehlendes `pipecat`-Submodul.

---

## 14. Port schon belegt

```bash
sudo ss -lptn | grep -E ':80|:443|:3010|:8000|:8787'
```

Anderen Dienst stoppen oder in `.env` `GUARDIAN_PORT=8788` setzen und neu deployen.

---

## 15. Docker / Compose fehlt

```bash
docker compose version
```

Wenn das fehlt: Docker Engine + Compose-Plugin installieren, User in Gruppe `docker`, neu einloggen.

---

## 16. Falsches Verzeichnis / COMPOSE_FILE vergessen

Immer aus dem Repo-Root (dort liegt `docker-compose.yaml`).

```bash
pwd
ls docker-compose.yaml custom/compose.overlay.yaml
echo "$COMPOSE_FILE"
```

`deploy.sh` setzt `COMPOSE_FILE` selbst. Manuelles `docker compose …` **muss** beide Dateien haben:

```bash
docker compose -f docker-compose.yaml -f custom/compose.overlay.yaml ps
```

---

## Schnellmatrix

| Du siehst | Wahrscheinlich | Befehl |
| --- | --- | --- |
| Overlay missing | Falscher Branch | `git checkout Guardian-Dograh` |
| PUBLIC_HOST fehlt | setup nicht gelaufen | `sudo ./setup_remote.sh` |
| Kein Deepgram EU | Stock-Image | `bash custom/scripts/deploy.sh remote` |
| Guardian unerreichbar | Firewall / Container | Port 8787 + `logs guardian` |
| API rot | Secret / Postgres | `logs api`, `.env` prüfen |
| Anruf ohne Ton | UDP/TURN zu | Ports 3478, 5349, 49152–49200 |
| Healthcheck 3 | Naht verloren | `SEAM_MAP.md`, nicht wegmergen |
| Healthcheck 4 | US-Deepgram editiert | File auf upstream zurücksetzen |
| Zertifikat-Warnung | Private IP | Einmal akzeptieren oder Domain |

Wenn nichts davon passt: Ausgabe von `bash custom/scripts/diagnose.sh` plus die letzten 80 Zeilen `logs api` aufheben — daran sieht man den Rest.
