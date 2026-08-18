# Pipecat Deepgram Client Konfiguration

Pipecat hat **drei** Deepgram-Services. Jeder baut den Client anders.
US-Deepgram in Dograh übergibt **keinen** Host (SDK-Default = `api.deepgram.com`).
Deepgram EU muss den Host **pro Service, mit dem richtigen Parameter** setzen.

Quelle im Overlay: [`factory.py`](factory.py), Konstanten: [`config.py`](config.py).
Pipecat-Code: `pipecat/services/deepgram/{stt,flux/stt,tts}.py`.

## 1. Nova STT — Deepgram SDK Client

Klasse: `pipecat.services.deepgram.stt.DeepgramSTTService`

| | |
| --- | --- |
| Parameter | `base_url` |
| Unser Wert | `https://api.eu.deepgram.com` |
| US-Default | `""` → SDK fällt auf `api.deepgram.com` |

Pipecat intern (`_derive_deepgram_urls` + `DeepgramClientEnvironment`):

```python
from deepgram import DeepgramClientEnvironment, AsyncDeepgramClient

ws_url, http_url = _derive_deepgram_urls(base_url)
# https://api.eu.deepgram.com →
#   http_url = https://api.eu.deepgram.com
#   ws_url   = wss://api.eu.deepgram.com

env = DeepgramClientEnvironment(
    base=http_url,
    production=ws_url,
    agent=ws_url,
    agent_rest=http_url,  # nur deepgram-sdk >= 7.2
)
client = AsyncDeepgramClient(api_key=api_key, environment=env)
```

Nicht tun:
- `environment=` selbst übergeben — der Konstruktor hat das Feld nicht.
- `wss://...` hier übergeben — funktioniert, aber HTTPS-Origin ist die offizielle Pipecat-Form.
- `base_url` leer lassen — dann landet der Call in den USA.

## 2. Flux STT — roher WebSocket, kein SDK

Klasse: `pipecat.services.deepgram.flux.stt.DeepgramFluxSTTService`

| | |
| --- | --- |
| Parameter | `url` (**nicht** `base_url`) |
| Unser Wert | `wss://api.eu.deepgram.com/v2/listen` |
| US-Default | `wss://api.deepgram.com/v2/listen` |

Pipecat intern:

```python
self._url = url
self._websocket_url = f"{self._url}?{self._build_query_string()}"
websocket = await self._websocket_connect(
    self._websocket_url,
    additional_headers={"Authorization": f"Token {api_key}"},
)
```

Nicht tun:
- `base_url=` setzen — Flux ignoriert das, bleibt auf US `/v2/listen`.
- Nur den Host ohne `/v2/listen` übergeben.

## 3. TTS — roher WebSocket, kein SDK

Klasse: `pipecat.services.deepgram.tts.DeepgramTTSService`

| | |
| --- | --- |
| Parameter | `base_url` |
| Unser Wert | `wss://api.eu.deepgram.com` |
| US-Default | `wss://api.deepgram.com` |

Pipecat intern:

```python
url = f"{self._base_url}/v1/speak?model=...&encoding=...&sample_rate=..."
headers = {"Authorization": f"Token {api_key}"}
websocket = await self._websocket_connect(url, additional_headers=headers)
```

Nicht tun:
- `https://...` übergeben — TTS hängt `/v1/speak` an und erwartet `wss://`.
- `wss://api.eu.deepgram.com/v1/speak` übergeben — sonst wird `/v1/speak` doppelt.

## 4. Mapping (verbindlich)

| Dograh-Modell | Pipecat-Klasse | Kwarg | Wert |
| --- | --- | --- | --- |
| `nova-3-*` | `DeepgramSTTService` | `base_url` | `https://api.eu.deepgram.com` |
| `flux-general-*` | `DeepgramFluxSTTService` | `url` | `wss://api.eu.deepgram.com/v2/listen` |
| Aura TTS | `DeepgramTTSService` | `base_url` | `wss://api.eu.deepgram.com` |
| Key-Check (kein Pipecat) | `DeepgramClient` | `environment` | `build_eu_environment()` |

## 5. Kontrolle

```bash
# Factory-Test: Nova bekommt https base_url, Flux bekommt url=wss .../v2/listen
python3 -m pytest custom/tests/test_deepgram_eu_factory.py -q
```

Runtime-Log bei `provider=deepgram_eu`:
- Nova: Deepgram-SDK Environment `api.eu.deepgram.com`
- Flux: WebSocket `wss://api.eu.deepgram.com/v2/listen?...`
- TTS: WebSocket `wss://api.eu.deepgram.com/v1/speak?...`

Erscheint `api.deepgram.com` ohne `.eu.`, ist der **US-Provider** gewählt oder ein Kwarg falsch.
