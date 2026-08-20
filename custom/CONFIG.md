# Was die Config wirklich macht

Zwei Ebenen:

1. **Was du in der UI setzt** (Agent-JSON + Overlay-Schema-Felder)
2. **Was die Factory verdrahtet** (Host, Listen-Flags, Fallback)

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
| `text_filters` | XML-Tags raus + **EmotionTextFilter** | Tool-Calls stumm; Default-Emotion-Tag wenn LLM keinen setzt |
| `skip_aggregator_types` | `recording_router`, `recording` | Recording nicht als TTS-Text |
| `silence_time_s` | `1.0` | Pause nach TTS |
| `prosody_speed` / `prosody_volume` | aus `speed` / `volume` | Mapping UI → Fish |
| ungültiges `latency` | → `balanced` | Fallback |

PCM/WSS kommt automatisch. Nötig sind Key + Voice + gewünschtes Modell/Sprache.

### Emotion-Tags (Lösung 1C — Safety Net)

Fish S2 liest `[bracket]`-Tags im gesprochenen Text. Der Agent-Prompt soll sie setzen;
die Factory hängt zusätzlich `EmotionTextFilter` an:

- Fehlt ein führendes `[…]` → wird `[friendly]` vorangestellt (Default).
- Ist schon ein Tag da (`[empathetic] …`) → unverändert.
- Code: `custom/processors/emotion_text_filter.py`

| Env / Attribut | Default | Wirkung |
| --- | --- | --- |
| `FISH_EMOTION_INJECT` | `1` | `0` / `false` schaltet den Injector aus |
| `FISH_EMOTION_DEFAULT_TAG` | `friendly` | Tag-Name ohne Klammern |
| `tts.emotion_inject` (optional) | an | per Agent-Config überschreiben |
| `tts.emotion_default_tag` (optional) | `friendly` | per Agent-Config überschreiben |

Prompt-Regeln bleiben sinnvoll (situative Tags). Der Filter ist nur die Absicherung.

## Deepgram STT

Deepgram 2 und Deepgram 3 sind **eigene Overlay-Provider** (nicht official US `deepgram`).
Live-Flags liegen in `custom/providers/deepgram_common.py` (`LIVE_STT_DEFAULTS`)
und sind im Schema als Bools sichtbar. Factory liest `getattr(stt, flag, default)`.

### UI / Agent-JSON

| Feld | Typisch | Anpassen? |
| --- | --- | --- |
| `provider` | `deepgram_2` oder `deepgram_3` | nie official `deepgram` für EU |
| `api_key` | Deepgram-Key | Pflicht |
| `model` | `nova-3-general` | oder Flux `flux-general-en` / `flux-general-multi` |
| `language` | `multi` | oder fest `de` / `en` |
| `smart_format` | `true` | Zahlen/Daten glätten |
| `interim_results` | `false` | Zwischenstände aus |
| `endpointing` | `true` → 100 ms | Ende der Äußerung |
| `keyterm_prompting` | `true` | Workflow-Keyterms |
| `diarize` | `true` | Sprecher trennen |
| `punctuate` | `true` | Satzzeichen |
| `profanity_filter` | `false` | |
| `redact` | `false` | PII |
| `replace` | `true` | Find and Replace (`settings.extra`) |
| `numerals` | nur `deepgram_3` | `true` |
| `vad_events` | nur `deepgram_3` | `true` (`extra`) |

### Factory — je nach Profil

Gemeinsam für Nova (nicht Flux):

- `base_url` aus `DEEPGRAM_BASE_URL` (Default Overlay: `api.eu.deepgram.com`)
- `sample_rate` = Pipeline-In
- `should_interrupt=False` (UserAggregator macht Barge-in)
- `language` Default `multi`

Official `deepgram` in `api/services/pipecat/service_factory.py` bleibt unverändert
und liest `DEEPGRAM_BASE_URL` **nicht**.

| | `deepgram` | `deepgram_2` | `deepgram_3` |
| --- | --- | --- | --- |
| host | US, fest | `DEEPGRAM_BASE_URL` → EU | `DEEPGRAM_BASE_URL` → EU |
| endpointing | 100 ms | 100 ms | 100 ms |
| smart_format | — | an | an |
| punctuate | — | an | an |
| numerals | — | — | an |
| interim_results | — | aus | aus |
| diarize | — | an | an |
| vad_events | — | — | an (`extra`) |
| keyterm | aus Workflow | aus Workflow, wenn Prompting an | aus Workflow, wenn Prompting an |
| redact / replace | — | `extra` | `extra` |

Flux-Modelle: `DeepgramFluxSTTService`, WS `wss://{host}/v2/listen`, Keyterms wenn Prompting an.

`deepgram_eu`: immer `api.eu.deepgram.com`, Settings wie official `deepgram` (nicht Profil 2/3).

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
| Neue-User-Defaults | STT=`deepgram`, TTS=ElevenLabs | nur frische Default-Configs — danach selbst auf 2/3 + Fish stellen |
| Fish API-Key | kein `FISH_API_KEY` Env | Key nur in Agent-TTS |
| `FISH_EMOTION_INJECT` | `1` | EmotionTextFilter an/aus |
| `FISH_EMOTION_DEFAULT_TAG` | `friendly` | Default-Tag ohne Klammern |

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
| Fish | Key, Voice, Modell, Sprache, optional Prosody/Latency | PCM, Sample-Rate, XML-Filter, Emotion-Injector, Silence |
| Deepgram STT | Provider 2/3, Key, Modell, Sprache, Live-Flags | EU-Host, Endpointing 100 ms, Format, Diarize, Keyterms |
| Deepgram TTS | Key + Voice; EU = Provider `deepgram_eu` | Region-WS, Filter, Silence |
