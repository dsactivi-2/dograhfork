# Dograh Custom Fork — Projektplan & Runbook

| Feld | Wert |
| --- | --- |
| Version | 1.0 |
| Stand Discovery | 2026-08-18, Upstream-SHA `689ca048bb0ab03183d6904b6c6eb6a405084dd0`, Release v1.45.0 |
| Architektur | **Option 1 — Clean Separation / Custom Overlay** |
| Ziel-Provider | `deepgram` (US, unverändert) + `deepgram_eu` (neu, permanent) |
| Deployment | VPS, Docker **build mode** |
| Lizenz Upstream | BSD 2-Clause |

Dieses Dokument ist die einzige erlaubte Ausführungsquelle für Menschen und
Guardian-Agents. Jeder Schritt ist nummeriert. Kein Schritt darf übersprungen
werden, nur weil er „offensichtlich“ wirkt.

---

## 0. Verbindliche Regeln

### 0.1 Was Option 1 bedeutet

1. Der originale Deepgram-Provider (`provider: "deepgram"`) bleibt **byte-genau
   unverändert**.
2. Alle eigenen Implementierungen liegen unter `custom/` im Fork.
3. Upstream-Dateien dürfen nur **minimale, markierte Nähte (Seams)** bekommen.
   Eine Naht ist maximal ein Import, ein Enum-Wert, ein Union-Eintrag oder ein
   `elif`-Zweig, der in `custom/` delegiert.
4. Es ist **verboten**, Deepgram US um ein `base_url`-Feld zu erweitern und
   damit einen einzigen Provider mit URL-Feld zu bauen. Die UI muss **zwei
   getrennte Einträge** zeigen: `Deepgram` und `Deepgram EU`.
5. Es ist **verboten**, eine Upstream-Datei nach `custom/` zu kopieren und dort
   als „unsere Version“ weiterzupflegen.

### 0.2 Harte Wahrheit aus der Discovery (nicht weichzeichnen)

Dograh hat **kein Plugin-API** für STT/TTS-Provider.

Deshalb ist 100 % Zero-Core-Touch **technisch unmöglich**. Wer das behauptet,
hat die Registry nicht gelesen. Option 1 heißt hier:

- 95 %+ der Logik in `custom/`
- 4–6 Kern-Dateien mit zusammen **unter 30 markierten Zeilen**
- diese Zeilen sind die einzigen erlaubten Konflikte bei Upstream-Merges

### 0.3 Marker für jede Naht

Jede geänderte Zeile in einer Upstream-Datei **muss** diesen Kommentar tragen:

```python
# CUSTOM-SEAM: deepgram_eu — do not delete on upstream merge
```

Oder als Block:

```python
# CUSTOM-SEAM-BEGIN: deepgram_eu
...
# CUSTOM-SEAM-END: deepgram_eu
```

Ein Guardian-Agent, der eine `CUSTOM-SEAM`-Zeile löscht, hat den Job
fehlgeschlagen.

---

## 1. Discovery-Ergebnis (verifiziert, nicht geraten)

Untersucht wurde `https://github.com/dograh-hq/dograh` am 2026-08-18.
Wenn ein späterer Agent feststellt, dass Pfade gewandert sind, muss er
**Phase 1.9** ausführen und dieses Kapitel aktualisieren, bevor er Code
schreibt.

### 1.1 Repo-Topologie

```
dograh/
├── api/                 # FastAPI-Backend (Python 3.13)
├── ui/                  # Next.js 15 Frontend
├── pipecat/             # Git-Submodule dograh-hq/pipecat
├── scripts/             # setup_remote.sh, start_docker.sh, …
├── docs/                # Mintlify
├── docker-compose.yaml
├── remote_up.sh         # --build vs default pull
└── AGENTS.md            # nur lokale Dev-Hinweise, kein Plugin-Hook
```

### 1.2 Wo Provider wirklich leben

| Schicht | Datei | Rolle |
| --- | --- | --- |
| Enum + Schema + Decorator-Registry | `api/services/configuration/registry.py` | **Zentrale Wahrheit.** `ServiceProviders`, `REGISTRY`, `@register_stt` / `@register_tts`, Pydantic-Unions `STTConfig` / `TTSConfig` |
| Modelle / Sprachen | `api/services/configuration/options/deepgram.py` | `DEEPGRAM_STT_MODELS`, Sprachen, Flux-Modelle |
| Defaults | `api/services/configuration/defaults.py` | Default-STT ist Deepgram US |
| Validierung beim Speichern | `api/services/configuration/check_validity.py` | `_validator_map["deepgram"]` → `_check_deepgram_api_key` |
| Runtime-Instanz | `api/services/pipecat/service_factory.py` | `create_stt_service`, `create_tts_service` — harte `if/elif` auf `provider` |
| Persistenz-Schema | `api/schemas/ai_model_configuration.py` | `BYOKPipelineAIModelConfiguration.stt: STTConfig` |
| UI-Schema-API | `api/routes/organization.py` | `GET /organizations/model-configurations/v2/defaults` → `_byok_provider_schemas()` iteriert `REGISTRY` |
| UI-Formular | `ui/src/components/ServiceConfigurationForm.tsx` | **generisch.** Liest Schemas vom Backend. Kein Hardcode der Provider-Liste. |
| Pipecat STT (US-Default) | `pipecat/.../deepgram/stt.py` | `base_url: str = ""` → SDK-Default = US `api.deepgram.com` |
| Pipecat Flux STT | `pipecat/.../deepgram/flux/stt.py` | `url: str = "wss://api.deepgram.com/v2/listen"` |
| Pipecat TTS | `pipecat/.../deepgram/tts.py` | `base_url: str = "wss://api.deepgram.com"` |

### 1.3 Was der originale Deepgram-Provider **nicht** hat

`DeepgramSTTConfiguration` und `DeepgramTTSConfiguration` in
`registry.py` haben **kein** `base_url`-Feld. Die US-URL sitzt implizit in
Pipecat / im Deepgram-SDK. ElevenLabs hat bereits ein `base_url` für EU
Residency — dieses Muster **nicht** auf Deepgram anwenden (würde nur einen
Dropdown-Eintrag erzeugen).

### 1.4 Wie die UI Provider sichtbar macht

1. Backend registriert eine Klasse mit `@register_stt` in `REGISTRY[ServiceType.STT]`.
2. `provider_model_config("Deepgram EU")` setzt den **Anzeigenamen** (`title`
   im JSON-Schema).
3. `GET /api/v1/organizations/model-configurations/v2/defaults` liefert
   `byok.pipeline.stt.<providerId> = model_json_schema()`.
4. `ServiceConfigurationForm.tsx` rendert daraus das Dropdown.

**Folge:** Wenn Registry + Union + Factory stimmen, braucht die UI **keine
Frontend-Änderung**. `ui/src/client/types.gen.ts` ist generiert und für das
Formular nicht zwingend.

### 1.5 Offizielle Deepgram-Endpunkte (nicht raten)

| Region | Host | Verwendung |
| --- | --- | --- |
| US (Upstream-Default) | `api.deepgram.com` | bleibt am originalen Provider |
| EU (unser Provider) | `api.eu.deepgram.com` | [Deepgram Custom Endpoints](https://developers.deepgram.com/reference/custom-endpoints) |
| AU (nicht Gegenstand) | `api.au.deepgram.com` | später analog möglich |

Konkrete Werte für Pipecat (nachzumessen in Phase 3.4):

| Dienst | Parametername in Pipecat | EU-Wert |
| --- | --- | --- |
| Nova STT | `base_url` | `https://api.eu.deepgram.com` (oder Host-only — `_derive_deepgram_urls` entscheidet) |
| Flux STT | `url` | `wss://api.eu.deepgram.com/v2/listen` |
| TTS WebSocket | `base_url` | `wss://api.eu.deepgram.com` |
| Key-Check (SDK) | Client-Environment | `api.eu.deepgram.com` |

### 1.6 Docker kopiert `custom/` **nicht** automatisch

`api/Dockerfile` kopiert nur:

```
COPY ./api ./api
COPY ./scripts ...
COPY ./docs ./docs
```

Ein Ordner `custom/` im Repo-Root ist im Image unsichtbar, solange nicht
eine Naht `COPY ./custom ./custom` ergänzt wird. Deshalb ist diese eine
Dockerfile-Zeile **Pflicht-Naht**, nicht optional.

`PYTHONPATH=/app` — Imports lauten `from custom....`.

### 1.7 Factory-Verhalten, das den neuen Provider sonst killt

In `create_stt_service` / `create_tts_service` endet jeder Dispatch mit:

```python
else:
    raise HTTPException(status_code=400, detail=f"Invalid STT provider ...")
```

Ohne `elif` für `deepgram_eu` erscheint der Provider in der UI, stirbt aber
beim ersten Call.

Zusätzlich: `stt_uses_external_turns()` prüft nur
`ServiceProviders.DEEPGRAM`. Flux-Modelle auf Deepgram EU müssen dort
ebenfalls erkannt werden, sonst bricht Turn-Detection.

`check_validity._validator_map` kennt `deepgram_eu` nicht. Ohne Eintrag
schlägt Speichern der Model Configuration fehl (`return False` →
„Invalid API key“).

`STTConfig` / `TTSConfig` sind geschlossene Pydantic-Discriminated-Unions.
Ohne Union-Eintrag antwortet `PUT .../model-configurations/v2` mit **422**.

### 1.8 Dateien, die ein Agent **nicht** anfassen darf für Deepgram EU

- `evals/stt/providers/deepgram_provider.py` (nur Benchmarks)
- `ui/src/components/VoiceSelector.tsx` (TTS-Stimmen-Picker, nicht STT-Registry)
- Originalklassen `DeepgramSTTConfiguration`, `DeepgramTTSConfiguration`
- Pipecat-Submodule-Dateien (kein Patch am Submodule, außer ein späterer
  Fall das ausdrücklich verlangt — dann eigener Fork von `dograh-hq/pipecat`)

### 1.9 Discovery-Wiederholung nach jedem großen Upstream-Update

Der Agent führt **in dieser Reihenfolge** aus:

```bash
rg -n "class ServiceProviders" api/services/configuration/registry.py
rg -n "def register_stt|STTConfig|class DeepgramSTT" api/services/configuration/registry.py
rg -n "DEEPGRAM.value|create_stt_service|create_tts_service|stt_uses_external_turns" api/services/pipecat/service_factory.py
rg -n "_byok_provider_schemas|model-configurations/v2/defaults" api/routes/organization.py
rg -n "DEEPGRAM.value|_check_deepgram" api/services/configuration/check_validity.py
rg -n "class DeepgramSTTService|base_url|def __init__" pipecat/src/pipecat/services/deepgram/stt.py
rg -n "url =|base_url" pipecat/src/pipecat/services/deepgram/flux/stt.py
rg -n "base_url" pipecat/src/pipecat/services/deepgram/tts.py
rg -n "COPY" api/Dockerfile
```

Weicht ein Pfad ab: RUNBOOK-Kapitel 1 aktualisieren, dann erst implementieren.

---

## 2. Repository-Setup (Fork, Branches, Remotes)

### 2.1 Voraussetzungen

- GitHub-Account mit Recht, `dograh-hq/dograh` zu forken.
- Lokales Git, SSH oder HTTPS.
- Der Fork muss **privat oder öffentlich** sein — für den VPS-Build muss der
  VPS den Fork klonen können (Deploy Key bei privatem Fork).

### 2.2 Fork erstellen

1. Im Browser: https://github.com/dograh-hq/dograh → **Fork**.
2. Owner = dein Account oder deine Org (nicht `dograh-hq`).
3. Repository-Name: `dograh` belassen.
4. **Copy the `main` branch only** ist erlaubt. Submodule `pipecat` kommt
   beim ersten `submodule update`.

### 2.3 Lokal klonen und Submodule holen

```bash
git clone --recurse-submodules git@github.com:<DEIN-USER>/dograh.git
cd dograh
git submodule update --init --recursive
test -f pipecat/src/pipecat/services/deepgram/stt.py
```

Schritt 4 muss eine echte Datei finden. Sonst ist das Submodule leer und
jeder Docker-Build scheitert.

### 2.4 Remotes zwingend so setzen

```bash
git remote -v
```

Erwartetes Soll:

| Remote | URL | Zweck |
| --- | --- | --- |
| `origin` | `git@github.com:<DEIN-USER>/dograh.git` | dein Fork |
| `upstream` | `https://github.com/dograh-hq/dograh.git` | offizielles Repo |

Falls `upstream` fehlt:

```bash
git remote add upstream https://github.com/dograh-hq/dograh.git
git fetch upstream
```

`origin` darf **niemals** auf `dograh-hq/dograh` zeigen.

### 2.5 Branch-Modell (verbindlich)

| Branch | Inhalt | Wer committet |
| --- | --- | --- |
| `main` | Exakte Kopie von `upstream/main`. Keine Custom-Commits. | nur Fast-Forward von upstream |
| `custom` | Langlebiger Arbeitsbranch. Enthält `custom/` + Seams. | alle Anpassungen |
| `custom/backup-YYYYMMDD` | Snapshot vor jedem Upstream-Merge | Guardian vor Update |

```bash
git checkout main
git fetch upstream
git merge --ff-only upstream/main
git push origin main

git checkout -b custom
git push -u origin custom
```

`main` bleibt der saubere Upstream-Spiegel. Deployed wird **nur** `custom`.

### 2.6 Schutz auf GitHub (manuell, einmalig)

1. Branch `custom` als Default-Branch des Forks setzen **oder** Default auf
   `main` lassen und auf dem VPS explizit `custom` auschecken. Empfehlung:
   Default = `custom`, damit `setup_remote.sh` den richtigen Branch klont.
2. Branch protection auf `custom`: keine Force-Pushes.
3. Deploy Key (read-only) für den VPS anlegen, wenn der Fork privat ist.

### 2.7 `.gitattributes` im Fork (Custom-Commit)

Datei `.gitattributes` im Repo-Root, Inhalt:

```
custom/** linguist-vendored=false
custom/** merge=ours
```

**Achtung:** `merge=ours` gilt nur, wenn lokal

```bash
git config merge.ours.driver true
```

gesetzt ist. Das verhindert, dass ein merkwürdiger Upstream-Pfad namens
`custom/` unsere Dateien überschreibt. Upstream hat diesen Ordner heute
nicht. Der Driver ist eine Sicherheitsleine, kein Ersatz für sorgfältiges
Mergen der Seams.

---

## 3. Empfohlene Ordnerstruktur

### 3.1 Soll-Struktur im Fork (nach Phase 4)

```
dograh/
├── custom/                              # Source of Truth — Upstream fasst das nie an
│   ├── README.md
│   ├── AGENTS.md                        # Kopie/Link auf dograh-guardian/AGENTS.md
│   ├── PROVIDER_CONTRACT.md
│   ├── __init__.py
│   ├── providers/
│   │   ├── __init__.py
│   │   └── deepgram_eu/
│   │       ├── __init__.py
│   │       ├── config.py                # IDs, URLs, Anzeigename
│   │       ├── schema.py                # Pydantic-Klassen, @register_stt/@register_tts
│   │       ├── factory.py               # create_stt / create_tts
│   │       └── validate.py              # API-Key-Check gegen EU-Host
│   ├── registry/
│   │   ├── __init__.py
│   │   └── register_custom_providers.py
│   ├── seams/
│   │   ├── README.md                    # welche Kernzeilen erlaubt sind
│   │   └── SEAM_MAP.md                  # Datei → Zeilenanker
│   ├── guardian/
│   │   ├── healthcheck.py
│   │   ├── update.sh
│   │   └── expected_manifest.json
│   └── tests/
│       ├── test_deepgram_eu_schema.py
│       └── test_deepgram_eu_factory.py
├── api/                                 # Upstream, plus Seams
├── ui/                                  # Upstream, keine Änderung für Deepgram EU
├── pipecat/                             # Submodule, keine Änderung
└── dograh-guardian/                     # dieses Runbook (darf auch nur im Fork-Root liegen)
    ├── RUNBOOK.md
    └── AGENTS.md
```

### 3.2 Regel für neue Dateien

| Ort | Erlaubt |
| --- | --- |
| `custom/**` | immer, ohne Limit |
| Datei aus `custom/seams/SEAM_MAP.md` | nur die dort gelisteten Zeilen |
| alles andere unter `api/`, `ui/`, `pipecat/` | **verboten** für diese Aufgabe |

### 3.3 `custom/providers/deepgram_eu/config.py` — feste Konstanten

Diese Werte sind die einzige Quelle für Hosts und IDs. Keine Magie in der Factory.

```python
PROVIDER_ID = "deepgram_eu"
PROVIDER_TITLE = "Deepgram EU"
HTTP_BASE_URL = "https://api.eu.deepgram.com"
WS_BASE_URL = "wss://api.eu.deepgram.com"
FLUX_LISTEN_URL = "wss://api.eu.deepgram.com/v2/listen"
DOCS_URL = "https://developers.deepgram.com/reference/custom-endpoints"
```

`PROVIDER_ID` darf **nicht** `"deepgram"` sein. Der Discriminator muss eindeutig
sein, sonst überschreibt die Registration den US-Provider in `REGISTRY`.

---

## 4. Umsetzung Provider „Deepgram EU“

Die Implementierung erfolgt erst nach Phase 2. Hier steht das exakte Soll.

### 4.1 Schema-Klassen in `custom/providers/deepgram_eu/schema.py`

1. `DeepgramEUSTTConfiguration` — Kopie der **Felder** von
   `DeepgramSTTConfiguration` (model, language, api_key), aber:
   - `provider: Literal["deepgram_eu"] = "deepgram_eu"`
   - `model_config = provider_model_config("Deepgram EU", provider_docs_url=DOCS_URL)`
   - Decorator `@register_stt`
2. `DeepgramEUTTSConfiguration` analog mit `@register_tts` und
   `provider: Literal["deepgram_eu"]`.
3. Die originalen Klassen **nicht importieren und ableiten, wenn das den
   Provider-Literal erbt**. Lieber komponieren: gleiche Felder neu deklarieren
   und Konstanten aus `options/deepgram.py` wiederverwenden
   (`DEEPGRAM_STT_MODELS`, `DEEPGRAM_LANGUAGES`, …). Das ist kein Fork der
   Klasse, sondern Wiederverwendung öffentlicher Konstanten.

### 4.2 Factory in `custom/providers/deepgram_eu/factory.py`

Funktionen:

- `create_deepgram_eu_stt(user_config, audio_config, keyterms=None)`
- `create_deepgram_eu_tts(user_config, audio_config)`
- `uses_external_turns(user_config) -> bool`

Verhalten:

1. Identisch zur US-Logik in `create_stt_service` für
   `ServiceProviders.DEEPGRAM`, **plus** EU-URL:
   - Flux-Modell → `DeepgramFluxSTTService(..., url=FLUX_LISTEN_URL)`
   - sonst → `DeepgramSTTService(..., base_url=HTTP_BASE_URL)`
2. TTS → `DeepgramTTSService(..., base_url=WS_BASE_URL)`
3. Vor dem ersten Merge: in der **exakten** Pipecat-Version des Submodules
   nachprüfen, ob `DeepgramFluxSTTService` den Parameter `url` oder `base_url`
   heißt (Discovery 1.5 / 1.9). Den tatsächlich existierenden Namen verwenden.
4. US-Factory-Code nicht ändern, außer dem einen `elif`-Seam.

### 4.3 Validator in `custom/providers/deepgram_eu/validate.py`

`_check_deepgram_api_key` im Core spricht den **US**-Host an
(`DeepgramClient(api_key=api_key)` ohne Environment). Für EU:

1. Eigenen Check schreiben, der denselben `projects.list()`-Call gegen
   `api.eu.deepgram.com` macht.
2. Deepgram-Doku: bestehende API-Keys funktionieren am EU-Endpoint.
3. Schlägt der EU-Check fehl, Fehlermeldung muss den Host nennen
   (`api.eu.deepgram.com`), nicht den US-Host.

### 4.4 Registrierung `custom/registry/register_custom_providers.py`

```text
register_all()
  1. importiert schema.py  → Decorator füllt REGISTRY
  2. hängt Validator in eine vom Seam gelesene Map ODER exportiert
     VALIDATOR = validate_deepgram_eu_key
  3. exportiert FACTORY_STT / FACTORY_TTS / uses_external_turns
```

Dieser Import **muss** laufen, bevor
`GET /model-configurations/v2/defaults` das erste Mal `REGISTRY` liest.
Deshalb der Seam in `registry.py` (unten).

### 4.5 Erlaubte Seams (vollständige Liste)

Mehr als diese Dateien anfassen = Architekturbruch.

#### Seam A — `api/services/configuration/registry.py`

Vier Kleinst-Edits:

1. Enum:

```python
DEEPGRAM = "deepgram"
DEEPGRAM_EU = "deepgram_eu"  # CUSTOM-SEAM: deepgram_eu — do not delete on upstream merge
```

2. `BaseServiceConfiguration.provider` Literal: `ServiceProviders.DEEPGRAM_EU`
   in die Literal-Liste aufnehmen. Marker-Kommentar daneben.

3. Nach den originalen Deepgram-Klassen, **bevor** `STTConfig`/`TTSConfig`
   gebaut werden:

```python
# CUSTOM-SEAM-BEGIN: deepgram_eu
from custom.providers.deepgram_eu.schema import (  # noqa: E402
    DeepgramEUSTTConfiguration,
    DeepgramEUTTSConfiguration,
)
# CUSTOM-SEAM-END: deepgram_eu
```

   Der Import triggert `@register_stt` / `@register_tts`.

4. In `STTConfig = Annotated[Union[...]]` und `TTSConfig = Annotated[Union[...]]`
   jeweils `DeepgramEUSTTConfiguration` / `DeepgramEUTTSConfiguration`
   einfügen, direkt hinter dem originalen Deepgram-Eintrag.

**Konflikt-Regel bei Upstream-Merge:** Neue Provider von Upstream **behalten**.
Unsere zwei Union-Zeilen und den Enum-Wert **behalten**. Niemals „theirs“ auf
die ganze Datei anwenden.

#### Seam B — `api/services/pipecat/service_factory.py`

1. Import:

```python
# CUSTOM-SEAM: deepgram_eu
from custom.providers.deepgram_eu.factory import (
    create_deepgram_eu_stt,
    create_deepgram_eu_tts,
    deepgram_eu_uses_external_turns,
)
```

2. In `stt_uses_external_turns`:

```python
if user_config.stt.provider == ServiceProviders.DEEPGRAM_EU.value:  # CUSTOM-SEAM
    return deepgram_eu_uses_external_turns(user_config)
```

3. In `create_stt_service`, **vor** dem finalen `else`:

```python
elif user_config.stt.provider == ServiceProviders.DEEPGRAM_EU.value:  # CUSTOM-SEAM
    return create_deepgram_eu_stt(user_config, audio_config, keyterms)
```

4. Analog in `create_tts_service`.

Den originalen `if provider == DEEPGRAM`-Block nicht anfassen.

#### Seam C — `api/services/configuration/check_validity.py`

Im `__init__` von `UserConfigurationValidator`, in `_validator_map`:

```python
ServiceProviders.DEEPGRAM_EU.value: self._check_deepgram_eu_api_key,  # CUSTOM-SEAM
```

Und eine dünne Methode, die nach `custom/` delegiert:

```python
def _check_deepgram_eu_api_key(self, model: str, api_key: str) -> bool:  # CUSTOM-SEAM
    from custom.providers.deepgram_eu.validate import check_deepgram_eu_api_key
    return check_deepgram_eu_api_key(api_key)
```

#### Seam D — `api/Dockerfile`

Direkt nach `COPY --chown=dograh:dograh ./api ./api`:

```
# CUSTOM-SEAM: deepgram_eu — overlay must be in the image
COPY --chown=dograh:dograh ./custom ./custom
```

Ohne diese Zeile existiert der Provider im Git, aber nicht im Container.

#### Seam E — nur falls PYTHONPATH in einem Worker nicht `/app` ist

Prüfen: `scripts/start_services_docker.sh`, `scripts/run_arq_worker.sh`.
Wenn dort `PYTHONPATH` hart auf `/app/api` gesetzt wird, `custom` zusätzlich
aufnehmen. Heute ist `PYTHONPATH=/app` im Dockerfile — dann ist Seam E
**nicht nötig**. Erst ändern, wenn der Import `from custom...` im Container
fehlschlägt.

### 4.6 Dateien, die bewusst **nicht** geändert werden

- `ui/**` — Schema kommt vom Backend.
- `api/services/configuration/defaults.py` — Default bleibt Deepgram US.
- `pipecat/**` — Parameter `base_url`/`url` reichen.
- `evals/**` — optional später, kein Blocker.

### 4.7 Tests (müssen mit ins `custom/`-Paket)

`custom/tests/test_deepgram_eu_schema.py`:

1. `REGISTRY[ServiceType.STT]` enthält `"deepgram"` **und** `"deepgram_eu"`.
2. `REGISTRY[ServiceType.STT]["deepgram"]` ist weiter `DeepgramSTTConfiguration`.
3. JSON-Schema von `deepgram_eu` hat `title == "Deepgram EU"`.
4. `STTConfig.model_validate({provider: "deepgram_eu", api_key: "k", model: "nova-3-general", language: "de"})` geht durch.
5. `STTConfig.model_validate({provider: "deepgram", ...})` geht weiter durch.

`custom/tests/test_deepgram_eu_factory.py`:

1. Mock `DeepgramSTTService` / `DeepgramFluxSTTService` / `DeepgramTTSService`.
2. Assert: EU-Factory übergibt `base_url`/`url` mit `api.eu.deepgram.com`.
3. Assert: US-Factory (`create_stt_service` mit `provider=deepgram`) übergibt
   **kein** EU-Host.

Ausführen (im Dev-venv, analog Dograh-AGENTS.md):

```bash
source venv/bin/activate
set -a && source api/.env.test && set +a
python -m pytest custom/tests -q
```

---

## 5. UI sichtbar und auswählbar machen

### 5.1 Erwartetes UI-Verhalten (Abnahme)

In **Model Configurations → BYOK → Pipeline → Transcriber (STT)**:

| Dropdown-Eintrag | `provider`-Wert im gespeicherten JSON | Host |
| --- | --- | --- |
| Deepgram | `deepgram` | `api.deepgram.com` |
| Deepgram EU | `deepgram_eu` | `api.eu.deepgram.com` |

Beide gleichzeitig vorhanden. Reihenfolge egal. Speichern beider Varianten
muss 200 liefern, nicht 422.

TTS analog, falls die Stimme ebenfalls über Deepgram läuft.

### 5.2 Warum kein UI-Patch nötig ist

`ServiceConfigurationForm.tsx` macht:

```ts
const providerSchema = schemas?.[service]?.[currentProvider];
```

`schemas.stt` kommt aus `_byok_provider_schemas(ServiceType.STT)`, und die
iteriert `REGISTRY[service_type].items()`. Sobald Seam A greift, erscheint
der Eintrag.

Der Anzeigename ist `model_config.title` = `"Deepgram EU"`, nicht der
rohe Key `deepgram_eu`.

### 5.3 Verifikation ohne Browser (auf dem VPS oder lokal)

```bash
# nach Login Cookie/JWT ersetzen
curl -sS -H "Authorization: Bearer $TOKEN" \
  "$BASE/api/v1/organizations/model-configurations/v2/defaults" \
  | python -c "import json,sys; d=json.load(sys.stdin); print(sorted(d['byok']['pipeline']['stt']))"
```

Soll enthalten: `deepgram` und `deepgram_eu`.

Titel prüfen:

```bash
... | python -c "import json,sys; d=json.load(sys.stdin); print(d['byok']['pipeline']['stt']['deepgram_eu']['title'])"
```

Soll: `Deepgram EU`.

### 5.4 Falls der Eintrag fehlt — Debug-Reihenfolge

1. Ist `custom/` im Container? `docker compose exec api ls /app/custom/providers/deepgram_eu`
2. Schlägt der Import fehl? `docker compose logs api | rg -i "custom|deepgram_eu|ImportError"`
3. Ist Seam A in der gebauten Image-Schicht? Image nach Codeänderung **neu
   gebaut** (`--build`), nicht nur neu gestartet?
4. Ist `DEEPGRAM_EU` im Enum? Sonst crasht der Import der Schema-Klasse.

### 5.5 Generierte TS-Typen

`ui/src/client/types.gen.ts` kennt `deepgram_eu` zunächst nicht. Das ist
kein Blocker, weil das Formular runtime-schemas nutzt. Nur wenn ein
Typecheck der UI durch einen späteren OpenAPI-Gen-Schritt bricht:

- nicht per Hand die 2000-Zeilen-Datei patchen
- OpenAPI-Gen des Projekts laufen lassen (siehe `scripts/` / CONTRIBUTING)
- oder den Gen-Schritt in der UI so belassen und den Check ignorieren, solange
  er nicht im Docker-Build der UI failt

---

## 6. Update-Strategie (Upstream sicher holen)

### 6.1 Wann updaten

- Nach einem Release auf https://github.com/dograh-hq/dograh/releases
- oder wenn ein benötigter Bugfix auf `main` liegt.

Nie blind täglich mergen, ohne Backup-Branch.

### 6.2 Ablauf — jedes Mal identisch

```bash
cd /path/to/dograh

# 0. Sauberer Tree
git status --porcelain
# muss leer sein. Sonst committen oder stashen. Nie mit dirty tree mergen.

# 1. Backup
git checkout custom
git branch "custom/backup-$(date +%Y%m%d-%H%M)"
git push origin "custom/backup-$(date +%Y%m%d-%H%M)"

# 2. Upstream holen
git fetch upstream --tags
git log --oneline HEAD..upstream/main | head

# 3. Spiegel-Branch fortschreiben
git checkout main
git merge --ff-only upstream/main
git push origin main

# 4. In custom mergen (NICHT rebase auf einem deployed Branch)
git checkout custom
git merge --no-ff upstream/main -m "merge(upstream): $(date +%Y-%m-%d)"
```

### 6.3 Konflikt-Matrix

| Datei | Strategie |
| --- | --- |
| `custom/**` | **ours.** Upstream hat dort nichts verloren. |
| Seam-Dateien aus Kapitel 4.5 | Manuell: Upstream-Änderungen übernehmen, `CUSTOM-SEAM`-Blöcke erhalten. |
| `pipecat` (Submodule-SHA) | Upstream-SHA übernehmen, danach `git submodule update --init --recursive` |
| alle anderen Upstream-Dateien | **theirs** / normale Merge-Auflösung |

Wenn Git `custom/` als Konflikt markiert, obwohl Upstream den Ordner nicht
hat: Merge abbrechen, Ursache klären. Nicht den Ordner löschen.

```bash
# Notbremse
git merge --abort
git checkout custom
```

Dann User benachrichtigen. Kein „halb gemerged, pushen wir schon“.

### 6.4 Nach erfolgreichem Merge

```bash
git submodule update --init --recursive
rg -n "CUSTOM-SEAM" api/services/configuration/registry.py \
                   api/services/pipecat/service_factory.py \
                   api/services/configuration/check_validity.py \
                   api/Dockerfile
test -d custom/providers/deepgram_eu
python -m pytest custom/tests -q
```

Alle vier Seam-Dateien müssen mindestens eine `CUSTOM-SEAM`-Zeile haben.
Sonst wurde die Naht beim Merge verschluckt → wieder einfügen aus dem
Backup-Branch.

### 6.5 Push und VPS

```bash
git push origin custom
```

Auf dem VPS: Phase 7.6.

### 6.6 Was niemals tun

- `git rebase upstream/main` auf `custom`, wenn der Branch schon auf dem VPS
  gebaut wurde (Force-Push zerstört History und Backups).
- `git checkout upstream/main -- api/services/configuration/registry.py`
  (überschreibt Seams restlos).
- Submodule-Working-Tree von Hand patchen und committen.

---

## 7. Deployment auf dem VPS (Build Mode)

### 7.1 VPS-Soll

| Anforderung | Wert |
| --- | --- |
| RAM | mindestens 8 GB |
| vCPU | mindestens 4 |
| Docker + Compose Plugin | installiert |
| Root/sudo | nötig für `setup_remote.sh` |
| Ports TCP | 80, 443, 3478, 5349 |
| Ports UDP | 3478, 5349, 49152–49200 |

Offizielle Anleitung:
https://docs.dograh.com/deployment/docker

### 7.2 Erstinstallation

Auf dem VPS als User mit sudo:

```bash
curl -o setup_remote.sh \
  https://raw.githubusercontent.com/dograh-hq/dograh/main/scripts/setup_remote.sh
chmod +x setup_remote.sh
sudo ./setup_remote.sh
```

Prompts **in dieser Reihenfolge**, so beantworten:

1. Public IP — echte öffentliche IPv4 des VPS.
2. TURN-Passwort — Enter für Default oder eigenes setzen.
3. **Deployment mode → `build`** (nicht Enter/prebuilt).
   Prebuilt zieht `ghcr.io/dograh-hq`-Images **ohne** `custom/`.
4. Wenn nach Owner/Name und Branch gefragt wird:
   - Owner/Name = `<DEIN-USER>/dograh`
   - Branch = `custom`
5. FastAPI-Worker — Enter (4) oder an CPU anpassen.

Das Script klont den Fork nach `./dograh`, schreibt `.env`, erzeugt
`docker-compose.override.yaml` mit lokalen `build:`-Direktiven und startet
via `remote_up.sh --build`.

Erster Build dauert mehrere Minuten (API-Image + UI-Image).

### 7.3 Kontrolle nach dem ersten Start

```bash
cd dograh
git remote -v          # origin = dein Fork
git branch --show-current   # muss custom sein
test -d custom/providers/deepgram_eu
sudo docker compose --profile remote ps
```

UI über `https://<SERVER-IP>` öffnen (oder die vom Setup gedruckte URL).
Dann Phase 5.1 / 5.3.

### 7.4 Warum nur Build Mode

| Mode | Image-Quelle | `custom/` enthalten? |
| --- | --- | --- |
| pull / prebuilt | `ghcr.io/dograh-hq` | **nein** |
| build | lokal aus dem Checkout | **ja**, wenn Seam D im Dockerfile ist |

Ein späterer Agent, der auf pull zurückstellt, hat Deepgram EU still
entfernt. Das ist ein P0-Fehler.

### 7.5 `.env` auf dem VPS

Wird vom Setup erzeugt. Nicht ins Git. Secrets nie in `custom/` ablegen.
Deepgram-Keys gehören in die UI (Model Configurations), nicht in `.env`.

### 7.6 Update auf dem VPS nach einem Git-Push

```bash
cd dograh
git fetch origin
git checkout custom
git pull --ff-only origin custom
git submodule update --init --recursive
test -d custom/providers/deepgram_eu
sudo docker compose --profile remote up -d --build
```

`--build` ist Pflicht. Ohne Rebuild läuft der alte Image-Layer.

Einzelne Services:

```bash
sudo docker compose --profile remote build api
sudo docker compose --profile remote up -d api
```

UI nur neu bauen, wenn `ui/` wirklich geändert wurde (für Deepgram EU
normalerweise nicht).

### 7.7 Rollback

```bash
cd dograh
git checkout custom/backup-YYYYMMDD-HHMM
git submodule update --init --recursive
sudo docker compose --profile remote up -d --build
```

Danach Ursache beheben, wieder auf `custom` wechseln.

---

## 8. Schutzmechanismen

### 8.1 Verzeichnis `custom/` ist unantastbar

- Kein Upstream-Pfad dieses Namens (Stand Discovery).
- `.gitattributes` `merge=ours` (Phase 2.7).
- Guardian-Healthcheck schlägt fehl, wenn der Ordner fehlt.

### 8.2 Seam-Manifest

`custom/guardian/expected_manifest.json` listet:

```json
{
  "provider_id": "deepgram_eu",
  "required_paths": [
    "custom/providers/deepgram_eu/config.py",
    "custom/providers/deepgram_eu/schema.py",
    "custom/providers/deepgram_eu/factory.py",
    "custom/providers/deepgram_eu/validate.py",
    "custom/registry/register_custom_providers.py"
  ],
  "required_seams": [
    "api/services/configuration/registry.py",
    "api/services/pipecat/service_factory.py",
    "api/services/configuration/check_validity.py",
    "api/Dockerfile"
  ],
  "forbidden_edits": [
    "api/services/configuration/options/deepgram.py"
  ],
  "marker": "CUSTOM-SEAM"
}
```

### 8.3 Healthcheck (`custom/guardian/healthcheck.py`)

Exit 0 nur wenn alle wahr sind:

1. Jeder `required_paths`-Eintrag existiert und ist nicht leer.
2. Jede Seam-Datei enthält den String `CUSTOM-SEAM` und `deepgram_eu`.
3. `forbidden_edits`: `git diff upstream/main -- <file>` ist leer (Datei
   identisch zu Upstream).
4. Import-Smoke (wenn Python-Env da ist):
   `REGISTRY[STT]` hat `deepgram` und `deepgram_eu`.
5. Optional live: Defaults-Endpoint enthält beide Keys.

Exit 2 = `custom/` beschädigt. Exit 3 = Seam verloren. Guardian darf in
diesen Fällen **nicht** weitermergen.

### 8.4 Pre-commit / Pre-push (empfohlen)

```bash
# custom/guardian als lokalen Hook
python custom/guardian/healthcheck.py
```

### 8.5 Was „unberührt“ konkret heißt

| Objekt | Unberührt bedeutet |
| --- | --- |
| Originaler Deepgram-Code | `git diff upstream/main --` auf den Deepgram-Blöcken in `registry.py` zeigt **nur** unsere benachbarten Seam-Zeilen, nicht geänderte US-Logik |
| `custom/` | kein Upstream-Commit, keine automatische Löschung |
| Pipecat-Submodule | SHA kommt von Upstream, Working Tree clean |

---

## 9. Vorbereitung für spätere Guardian-Agents

### 9.1 Auftrag an jeden zukünftigen Bot

Lies zuerst:

1. `dograh-guardian/AGENTS.md`
2. dieses `RUNBOOK.md`
3. `custom/seams/SEAM_MAP.md` (nach der ersten Implementierung erzeugt)

### 9.2 Erlaubte autonome Aktionen

- Healthcheck ausführen und Report schreiben.
- `git fetch upstream` und Changelog `HEAD..upstream/main` zusammenfassen.
- Backup-Branch erzeugen.
- Merge **nur** wenn `git merge` konfliktfrei ist **und** Healthcheck danach
  grün ist.
- VPS-Rebuild anstoßen, wenn der User das in der Session erlaubt hat.

### 9.3 Pflicht-Stopp (Mensch holen)

- Konflikt in einer Seam-Datei.
- Upstream hat selbst einen Provider `deepgram_eu` oder ein `base_url` an
  Deepgram gebaut (dann Strategie neu bewerten, nicht stumm mergen).
- Healthcheck Exit ≠ 0.
- Dockerfile-COPY für `custom/` wurde von Upstream umgebaut.
- `REGISTRY`-Mechanismus wurde ersetzt.

### 9.4 Report-Format nach jedem Agent-Lauf

Datei `custom/guardian/last_report.md`:

```
Datum:
Agent:
Aktion: healthcheck | update | implement | rollback
Upstream SHA vorher/nachher:
custom/ intakt: ja/nein
Seams vorhanden: ja/nein
Defaults-Endpoint deepgram_eu: ja/nein/nicht geprüft
Nächster menschlicher Schritt:
```

### 9.5 Weitere Custom-Provider später

Kopiere `custom/providers/deepgram_eu/` nach
`custom/providers/<name>/`, neue `PROVIDER_ID`, neue Seams analog.
Nicht den Deepgram-EU-Code verbiegen, damit er „generisch“ wird, bevor ein
zweiter Provider existiert.

---

## 10. Checkliste „Was ist fertig, wenn…“

Das System ist fertig, wenn **alle** Kästchen wahr sind. Ein offenes
Kästchen = nicht fertig.

- [ ] Fork existiert unter `<DEIN-USER>/dograh`, nicht unter `dograh-hq`.
- [ ] `git remote origin` = Fork, `git remote upstream` = `dograh-hq/dograh`.
- [ ] Branch `main` ist Fast-Forward von `upstream/main`.
- [ ] Branch `custom` existiert, ist Default oder explizit auf dem VPS aktiv.
- [ ] `custom/providers/deepgram_eu/` enthält config, schema, factory, validate.
- [ ] Originaler Provider-Key ist weiter `"deepgram"`.
- [ ] Neuer Provider-Key ist `"deepgram_eu"`.
- [ ] Alle vier Seams (registry, factory, check_validity, Dockerfile) tragen `CUSTOM-SEAM`.
- [ ] `pytest custom/tests` ist grün.
- [ ] VPS läuft im **build**-Modus (`docker-compose.override.yaml` existiert).
- [ ] Image enthält `/app/custom`.
- [ ] UI-Dropdown zeigt **Deepgram** und **Deepgram EU**.
- [ ] Speichern von Deepgram EU liefert kein 422.
- [ ] Runtime-STT/TTS für Deepgram EU verwendet `api.eu.deepgram.com` (Log oder Test-Double).
- [ ] Runtime für Deepgram US verwendet **nicht** den EU-Host.
- [ ] Ein Probe-Merge-Dry-Run (`git merge --no-commit --no-ff upstream/main` auf einem
      Wegwerf-Branch) löscht `custom/` nicht.
- [ ] `custom/guardian/healthcheck.py` Exit 0.
- [ ] `custom/guardian/last_report.md` existiert nach dem letzten Agent-Lauf.
- [ ] Dieses Runbook liegt im Fork und beschreibt die tatsächlich gebauten Pfade.

---

## 11. Verbotene Handlungen (noch einmal, ohne Interpretation)

1. Originalen Deepgram-Provider ändern (URL, Felder, Defaults).
2. Core-Dateien großflächig patchen oder umformatieren „während wir sowieso da sind“.
3. `custom/` in `main` mergen und danach den Ordner von `custom` löschen.
4. Prebuilt/pull-Images für diesen Fork verwenden.
5. Lösungen vorschlagen, die nach jedem Upstream-Update manuell neu angewendet
   werden müssen (Patch-Dateien auf US-Deepgram, sed-Scripts auf registry.py).
6. Force-Push auf `custom` ohne expliziten User-Befehl.
7. Pipecat-Submodule forken, solange `base_url`/`url` ausreichen.
8. Einen einzelnen Deepgram-Eintrag mit URL-Feld als „EU-Lösung“ verkaufen.

---

## Anhang A — Konkrete nächste Ausführungsreihenfolge

Wenn der User sagt „setz um“, arbeitet der Agent **genau** so:

1. Phase 2 (Fork/Remotes/Branch) — nichts committen, das nicht existiert.
2. Phase 1.9 noch einmal gegen den ausgecheckten Tree.
3. `custom/`-Gerüst anlegen (Phase 3).
4. Schema + Config schreiben, Tests für Registry-Keys (rot, weil Seams fehlen).
5. Seams A–D setzen.
6. Tests grün.
7. Factory + Validator + Tests.
8. Healthcheck + SEAM_MAP.md schreiben.
9. Push auf `origin/custom`.
10. Phase 7 auf dem VPS (oder Anleitung an den User, falls kein VPS-Zugang).
11. Phase 5.3 Verifikation.
12. Phase-10-Checkliste ausfüllen.

Kein Schritt 10 vor Schritt 7. Kein „UI erstmal mocken“.

## Anhang B — Referenzlinks

- Repo: https://github.com/dograh-hq/dograh
- Docker Remote: https://docs.dograh.com/deployment/docker
- Deepgram EU Host: https://developers.deepgram.com/reference/custom-endpoints
- Transcriber-Doku: https://docs.dograh.com/configurations/transcriber
- Setup-Befehl: `curl -o setup_remote.sh https://raw.githubusercontent.com/dograh-hq/dograh/main/scripts/setup_remote.sh && chmod +x setup_remote.sh && sudo ./setup_remote.sh`
