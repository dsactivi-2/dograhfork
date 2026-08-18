# Was die Config wirklich macht

Zwei Ebenen:

1. **Was du in der UI setzt**
2. **Was die Factory fest verdrahtet** (nicht in der UI, aber aktiv)

Keys nur in der Agent-Config. Kein `FISH_API_KEY` in der Shell.

## Fish Audio TTS

### UI / Agent-JSON (anpassbar)

| Feld | Typisch | Warum anfassen |
| --- | --- | --- |
| `api_key` | Fish-Key | Pflicht |
| `voice` | `reference_id` | Pflicht — ohne Voice **400** |
| `model` | `s2.1-pro` setzen | Image-Default ist noch `s2-pro` |
| `language` | `de` / `bs` / `hr` / `sr` | Default `en` |
| `latency` | `balanced` | Telephony; `normal` = schneller, unruhiger |
| `speed` | `1.0` | nur wenn zu schnell/langsam |
| `volume` | `0` | nur bei zu leise/laut |
| `normalize` | `true` | meist lassen |

### Factory — fest, nicht in der UI

| Setting | Wert | Bedeutung |
| --- | --- | --- |
| `output_format` | `pcm` | kein MP3 |
| `sample_rate` | Pipeline `transport_out_*` | WebRTC oft 16k, Telefon oft 8k |
| `text_filters` | XML-Function-Tags raus | Tool-Calls nicht vorlesen |
| `skip_aggregator_types` | `recording_router`, `recording` | Recording nicht als TTS-Text |
| `silence_time_s` | `1.0` | Pause nach TTS |
| `prosody_speed` / `prosody_volume` | aus `speed` / `volume` | Mapping UI → Fish |
| ungültiges `latency` | → `balanced` | Fallback |

PCM/WSS kommt automatisch. Nötig sind Key + Voice + gewünschtes Modell/Sprache.

## Deepgram STT

### UI / Agent-JSON

| Feld | Typisch | Anpassen? |
| --- | --- | --- |
| `provider` | `deepgram_3` statt `deepgram` | anderes Live-Profil |
| `api_key` | Deepgram-Key | Pflicht |
| `model` | `nova-3-general` | oder Flux `flux-general-en` / `flux-general-multi` |
| `language` | `multi` | oder fest `de` / `en` |

Mehr STT-Felder gibt die UI nicht. Den Rest setzt die Factory.

### Factory — je nach Profil (nicht in der UI)

Gemeinsam für Nova (nicht Flux):

- `base_url` aus `DEEPGRAM_BASE_URL` (Default Overlay: `api.eu.deepgram.com`)
- `sample_rate` = Pipeline-In
- `should_interrupt=False` (UserAggregator macht Barge-in)
- `language` Default `multi`
- `profanity_filter=False`

Official `deepgram` liest `DEEPGRAM_BASE_URL` **nicht**.

| | `deepgram` | `deepgram_2` | `deepgram_3` |
| --- | --- | --- | --- |
| endpointing | 100 ms | 100 ms | 400 ms |
| smart_format | — | an | an |
| punctuate | — | an | an |
| numerals | — | — | an |
| interim_results | — | an | aus |
| diarize | — | — | aus |
| vad_events | — | — | an (`extra`) |
| keyterm | aus Workflow | aus Workflow | nicht gesetzt |
| utterance_end_ms | — | — | nicht gesetzt |

Flux-Modelle: `DeepgramFluxSTTService`, WS `wss://{host}/v2/listen`.

`deepgram_eu`: immer `api.eu.deepgram.com`, Settings wie official `deepgram` (nicht Profil 3).

## Deepgram TTS (nur wenn nicht Fish)

UI: `api_key` + `voice` (z. B. `aura-2-helena-en`). Modell aus Voice (`aura-2` / `aura-1`).

Factory zusätzlich (Overlay `deepgram_eu`):

- TTS-WS auf EU-Host
- `text_filters` + `skip_aggregator_types` + `silence_time_s=1.0`

Official Deepgram-TTS bleibt US. Für EU-TTS **Deepgram EU** wählen.

## Plattform / Env (nicht Agent-JSON)

| Setting | Wert | Betrifft |
| --- | --- | --- |
| `DEEPGRAM_BASE_URL` | Default Overlay `api.eu.deepgram.com` | nur `deepgram_2` / `deepgram_3` Inference |
| Deepgram Key-Check | immer US `api.deepgram.com` | nur Validierung |
| Neue-User-Defaults | STT=`deepgram`, TTS=ElevenLabs | nur frische Default-Configs — danach selbst auf 3 + Fish stellen |
| Fish | kein `FISH_*` Env | Key nur in Agent-TTS |

## Typisch setzen

```json
{
  "stt": {
    "provider": "deepgram_3",
    "api_key": "DEIN_DEEPGRAM_KEY",
    "model": "nova-3-general",
    "language": "multi"
  },
  "tts": {
    "provider": "fish_audio",
    "api_key": "DEIN_FISH_KEY",
    "model": "s2.1-pro",
    "voice": "<eure reference_id>",
    "language": "de",
    "latency": "balanced"
  }
}
```

## Kurz

| | UI anfassen | Factory schon fest |
| --- | --- | --- |
| Fish | Key, Voice, Modell, Sprache, optional Prosody/Latency | PCM, Sample-Rate, Filter, Silence |
| Deepgram STT | Provider-Profil, Key, Modell, Sprache | EU-Host (2/3), Endpointing, Format, VAD, Interim je Profil |
| Deepgram TTS | Key + Voice; EU = Provider `deepgram_eu` | Region-WS, Filter, Silence |
