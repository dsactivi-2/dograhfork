# Seam map (Guardian-Dograh)

| ID | File | What the seam does | Marker |
| --- | --- | --- | --- |
| A1 | `api/services/configuration/registry.py` | Enum: `DEEPGRAM_EU`, `DEEPGRAM_2`, `DEEPGRAM_3`, `FISH_AUDIO` | `CUSTOM-SEAM` |
| A2 | `api/services/configuration/registry.py` | Literal on `BaseServiceConfiguration.provider` | `CUSTOM-SEAM` |
| A4 | `api/services/configuration/registry.py` | Import EU + 2 + 3 + Fish schema classes | `CUSTOM-SEAM-BEGIN` |
| A5 | `api/services/configuration/registry.py` | `TTSConfig` union: EU + Fish | `CUSTOM-SEAM` |
| A6 | `api/services/configuration/registry.py` | `STTConfig` union: EU + Deepgram 2 + Deepgram 3 | `CUSTOM-SEAM` |
| B1 | `api/services/pipecat/service_factory.py` | Import factory helpers | `CUSTOM-SEAM` |
| B2 | `api/services/pipecat/service_factory.py` | `stt_uses_external_turns` EU / 2 / 3 | `CUSTOM-SEAM` |
| B3 | `api/services/pipecat/service_factory.py` | `create_stt_service` EU / 2 / 3 elifs | `CUSTOM-SEAM` |
| B4 | `api/services/pipecat/service_factory.py` | `create_tts_service` EU + Fish elifs | `CUSTOM-SEAM` |
| C | `api/services/configuration/check_validity.py` | Validators delegate to `custom/` | `CUSTOM-SEAM` |
| D1 | `api/Dockerfile` | `COPY ./custom ./custom` | `CUSTOM-SEAM` |
| D2 | `api/Dockerfile` | `apply_branding.py` after `COPY docs` | `CUSTOM-SEAM` |

Official Deepgram (`options/deepgram.py` + factory US branch) stays byte-identical.

After every upstream merge: `rg -n "CUSTOM-SEAM"` must still hit every row.
`python3 custom/guardian/healthcheck.py` must exit 0.
