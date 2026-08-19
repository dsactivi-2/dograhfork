# Deepgram EU Endpoint Setup

Offizielle Quelle:
- https://developers.deepgram.com/reference/custom-endpoints
- https://developers.deepgram.com/reference/regional-endpoints

Keine Extra-Aktivierung, keine Warteliste. Derselbe API-Key wie US.

## 1. Endpunkte (fest in `config.py`)

| Dienst | Parameter in Pipecat | Wert |
| --- | --- | --- |
| Nova STT | `DeepgramSTTService(base_url=)` | `https://api.eu.deepgram.com` |
| Flux STT | `DeepgramFluxSTTService(url=)` | `wss://api.eu.deepgram.com/v2/listen` |
| TTS | `DeepgramTTSService(base_url=)` | `wss://api.eu.deepgram.com` |
| Key-Check (SDK) | `DeepgramClientEnvironment` | `base=https://api.eu.deepgram.com`, `production=wss://api.eu.deepgram.com` |

Pipecat leitet aus `base_url` selbst `https` + `wss` ab. US-Deepgram bekommt **keinen** dieser Werte.

## 2. In der Dograh-UI

1. Model Configurations → BYOK → Pipeline.
2. Transcriber: **Deepgram EU** (nicht „Deepgram“).
3. Modell: `nova-3-general` oder `flux-general-en` / `flux-general-multi`. Nicht Whisper.
4. Denselben Deepgram-API-Key eintragen wie für US.
5. Speichern. 422 = Seam A (Union) fehlt. „Invalid API key“ mit Host `api.eu.deepgram.com` = Key-Problem, nicht US-Host.
6. Optional TTS ebenfalls **Deepgram EU**.

## 3. Kontrolle ohne Browser

```bash
# nach Login
curl -sS -H "Authorization: Bearer $TOKEN" \
  "$BASE/api/v1/organizations/model-configurations/v2/defaults" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['byok']['pipeline']['stt']['deepgram_eu']['title'])"
# erwartet: Deepgram EU
```

Runtime-Log muss `api.eu.deepgram.com` zeigen, nie `api.deepgram.com`, wenn der Call über `deepgram_eu` läuft.

## 4. Was du nicht tun darfst

- Originalen Provider `deepgram` um ein URL-Feld erweitern.
- `DEEPGRAM_BASE_URL` als Env setzen, das US und EU vermischt.
- Whisper-Modelle auf EU erwarten — offiziell nicht verfügbar.
