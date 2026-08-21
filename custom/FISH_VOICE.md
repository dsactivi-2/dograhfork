# Fish Audio Voice-ID Setup

`voice` in Dograh ist Fish `reference_id` — eine 32-Zeichen-Hex-ID.
Nicht der Modellname (`s2.1-pro`). Nicht der Anzeigename der Stimme.

Ohne diese ID: Factory **400** („requires a voice“).

## 1. API-Key

1. [fish.audio/app/api-keys](https://fish.audio/app/api-keys/)
2. Key anlegen, kopieren.
3. In Dograh: Agent → TTS = **Fish Audio** → Feld `api_key`.

Kein `FISH_API_KEY` in `.env` nötig (nur für das Listen-Skript unten).

## 2. Voice-ID holen

### Variante A — fertige Stimme aus der Library

1. [fish.audio](https://fish.audio) → Stimme öffnen.
2. URL sieht so aus: `https://fish.audio/m/ca3007f96ae7499ab87d27ea3599956a`
3. Der Teil nach `/m/` **ist** die Voice-ID.
4. Oder den **Copy**-Button auf der Stimme nutzen.

Beispiele (öffentlich):

| Stimme (Beispiel) | Voice-ID |
| --- | --- |
| Library-Beispiel | `ca3007f96ae7499ab87d27ea3599956a` |
| Library-Beispiel | `9a9cf47702da476aa4629e2506d4a857` |

### Variante B — eigene Stimme klonen

1. Fish Dashboard → Voice Clone.
2. 15–60 s sauberes Sprechen hochladen.
3. Nach dem Training: ID aus der Stimmen-URL oder Copy.

### Variante C — eigene IDs auflisten

```bash
export FISH_API_KEY='dein-key'
bash custom/scripts/list_fish_voices.sh
```

Ausgabe: `id<TAB>title`. Die `id` kommt ins Feld `voice`.

## 3. In Dograh eintragen

Agent → TTS:

| Feld | Wert |
| --- | --- |
| provider | Fish Audio |
| api_key | Fish-Key |
| voice | die Hex-ID (z. B. `c737db0b875d4d0d88af86b7529e8fa1`) |
| model | `s2.1-pro` |
| language | `de` (oder `bs` / `hr` / `sr`) |
| latency | `balanced` |

Oder JSON:

```json
"tts": {
  "provider": "fish_audio",
  "api_key": "DEIN_FISH_KEY",
  "model": "s2.1-pro",
  "voice": "c737db0b875d4d0d88af86b7529e8fa1",
  "language": "de",
  "latency": "balanced"
}
```

Speichern → Key-Check läuft gegen `https://api.fish.audio/model`.

## 4. Prüfen

| Symptom | Ursache |
| --- | --- |
| 400 requires a voice | `voice` leer |
| Key-Check rot | falscher/abgelaufener Key |
| Falsche Stimme | Anzeigename statt ID, oder `model` ins Voice-Feld |
| Default-Englisch | `language` nicht gesetzt (Default `en`) |
| Roboter / MP3-Artefakte | Factory setzt PCM selbst — nicht anfassen |

STT bleibt getrennt: typisch `deepgram_3` + dieser Fish-TTS-Block.

Mehr Factory-Details: [CONFIG.md](./CONFIG.md).
