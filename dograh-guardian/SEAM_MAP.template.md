# Seam map (fill after first implementation)

Copy this file into the fork as `custom/seams/SEAM_MAP.md` and replace
`TBD` with real line numbers from the built tree.

| ID | File | What the seam does | Marker |
| --- | --- | --- | --- |
| A1 | `api/services/configuration/registry.py` | `ServiceProviders.DEEPGRAM_EU = "deepgram_eu"` | `CUSTOM-SEAM` |
| A2 | `api/services/configuration/registry.py` | Literal on `BaseServiceConfiguration.provider` | `CUSTOM-SEAM` |
| A3 | `api/services/configuration/registry.py` | Import `DeepgramEUSTTConfiguration` / `DeepgramEUTTSConfiguration` | `CUSTOM-SEAM-BEGIN` |
| A4 | `api/services/configuration/registry.py` | Add classes to `STTConfig` / `TTSConfig` unions | `CUSTOM-SEAM` |
| B1 | `api/services/pipecat/service_factory.py` | Import factory helpers | `CUSTOM-SEAM` |
| B2 | `api/services/pipecat/service_factory.py` | `stt_uses_external_turns` branch | `CUSTOM-SEAM` |
| B3 | `api/services/pipecat/service_factory.py` | `create_stt_service` elif | `CUSTOM-SEAM` |
| B4 | `api/services/pipecat/service_factory.py` | `create_tts_service` elif | `CUSTOM-SEAM` |
| C1 | `api/services/configuration/check_validity.py` | `_validator_map` entry | `CUSTOM-SEAM` |
| C2 | `api/services/configuration/check_validity.py` | `_check_deepgram_eu_api_key` | `CUSTOM-SEAM` |
| D1 | `api/Dockerfile` | `COPY ./custom ./custom` | `CUSTOM-SEAM` |

After every upstream merge: `rg -n "CUSTOM-SEAM"` must still hit every row.
