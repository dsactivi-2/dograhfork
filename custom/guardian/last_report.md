Datum: 2026-08-18
Agent: Grok Build / Dograh Guardian
Aktion: document (Pipecat Deepgram Client Konfiguration)
Upstream SHA vorher/nachher: 689ca048 (unverändert)
custom/ intakt: ja
Seams vorhanden: ja
Nova STT: DeepgramSTTService(base_url=https://api.eu.deepgram.com) → SDK DeepgramClientEnvironment
Flux STT: DeepgramFluxSTTService(url=wss://api.eu.deepgram.com/v2/listen) → raw WS
TTS: DeepgramTTSService(base_url=wss://api.eu.deepgram.com) → raw WS + /v1/speak
Nächster menschlicher Schritt: In UI Deepgram EU wählen; Flux nicht mit base_url konfigurieren
