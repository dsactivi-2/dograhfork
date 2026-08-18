# Seam map (built 2026-08-18, upstream SHA 689ca048)

| ID | File | Lines | What the seam does | Marker |
| --- | --- | --- | --- | --- |
| A1 | `api/services/configuration/registry.py` | 71 | `ServiceProviders.DEEPGRAM_EU = "deepgram_eu"` | `CUSTOM-SEAM` |
| A2 | `api/services/configuration/registry.py` | 72 | `ServiceProviders.FISH_AUDIO = "fish_audio"` | `CUSTOM-SEAM` |
| A3 | `api/services/configuration/registry.py` | 110–111 | Literal on `BaseServiceConfiguration.provider` | `CUSTOM-SEAM` |
| A4 | `api/services/configuration/registry.py` | 968–974 | Import EU + Fish schema classes | `CUSTOM-SEAM-BEGIN` |
| A5 | `api/services/configuration/registry.py` | 1478–1479 | `TTSConfig` union entries | `CUSTOM-SEAM` |
| A6 | `api/services/configuration/registry.py` | 1899 | `STTConfig` union entry | `CUSTOM-SEAM` |
| B1 | `api/services/pipecat/service_factory.py` | 21–27 | Import factory helpers | `CUSTOM-SEAM` |
| B2 | `api/services/pipecat/service_factory.py` | 232 | `stt_uses_external_turns` EU branch | `CUSTOM-SEAM` |
| B3 | `api/services/pipecat/service_factory.py` | 556 | `create_stt_service` EU elif | `CUSTOM-SEAM` |
| B4 | `api/services/pipecat/service_factory.py` | 927 | `create_tts_service` EU elif | `CUSTOM-SEAM` |
| B5 | `api/services/pipecat/service_factory.py` | 929 | `create_tts_service` Fish Audio elif | `CUSTOM-SEAM` |
| C1 | `api/services/configuration/check_validity.py` | 42 | `_validator_map` Deepgram EU | `CUSTOM-SEAM` |
| C2 | `api/services/configuration/check_validity.py` | 43 | `_validator_map` Fish Audio | `CUSTOM-SEAM` |
| C3 | `api/services/configuration/check_validity.py` | 316–323 | Thin validators that delegate to `custom/` | `CUSTOM-SEAM` |
| D1 | `api/Dockerfile` | 144–145 | `COPY ./custom ./custom` | `CUSTOM-SEAM` |
| D2 | `api/Dockerfile` | 174–175 | `apply_branding.py` after `COPY docs` | `CUSTOM-SEAM` |

Branding content itself is **not** a core edit source of truth. It lives in
`custom/branding/docs_overlay.json` and is written into `docs/docs.json` by
`custom/guardian/apply_branding.py`.

After every upstream merge: `rg -n "CUSTOM-SEAM"` must still hit every row.
