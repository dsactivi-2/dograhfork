import pytest
from pydantic import ValidationError

from api.services.configuration.options import DEEPGRAM_FLUX_MODELS, DEEPGRAM_REGIONS
from api.services.configuration.registry import (
    DeepgramSTTConfiguration,
    DeepgramTTSConfiguration,
)


def _schema_enum_or_examples(schema: dict) -> set[str]:
    values = schema.get("enum") or schema.get("examples") or []
    return {str(item) for item in values}


def test_deepgram_stt_schema_exposes_region_and_hides_nova_flags_on_flux():
    schema = DeepgramSTTConfiguration.model_json_schema()["properties"]

    assert schema["region"]["default"] == "us"
    assert _schema_enum_or_examples(schema["region"]) >= set(DEEPGRAM_REGIONS)

    for flag in (
        "smart_format",
        "punctuate",
        "interim_results",
        "diarize",
        "vad_events",
        "endpointing",
    ):
        hidden = schema[flag].get("hidden_for_models")
        assert hidden is not None
        assert set(hidden) == set(DEEPGRAM_FLUX_MODELS)

    assert schema["numerals"].get("type") == "boolean"
    assert "hidden_for_models" not in schema["numerals"]
    assert schema["endpointing"]["default"] == 100
    assert schema["endpointing"]["minimum"] == 10
    assert schema["endpointing"]["maximum"] == 5000


def test_legacy_saved_json_without_new_keys_gets_previous_factory_defaults():
    restored = DeepgramSTTConfiguration.model_validate(
        {
            "provider": "deepgram",
            "api_key": "test-key",
            "model": "nova-3-general",
            "language": "multi",
        }
    )
    assert restored.region == "us"
    assert restored.endpointing == 100
    assert restored.smart_format is False
    assert restored.punctuate is False
    assert restored.numerals is False
    assert restored.interim_results is False
    assert restored.diarize is False
    assert restored.vad_events is False


def test_deepgram_stt_rejects_invalid_region_and_endpointing():
    with pytest.raises(ValidationError):
        DeepgramSTTConfiguration(
            api_key="test-key",
            model="nova-3-general",
            region="asia",
        )
    with pytest.raises(ValidationError):
        DeepgramSTTConfiguration(
            api_key="test-key",
            model="nova-3-general",
            endpointing=9,
        )


def test_deepgram_stt_configuration_round_trip_persists_ui_flags():
    config = DeepgramSTTConfiguration(
        api_key="test-key",
        model="nova-3-general",
        language="de",
        region="eu",
        smart_format=True,
        punctuate=True,
        numerals=True,
        interim_results=False,
        diarize=False,
        vad_events=True,
        endpointing=400,
    )
    dumped = config.model_dump()
    restored = DeepgramSTTConfiguration.model_validate(dumped)

    assert restored.region == "eu"
    assert restored.smart_format is True
    assert restored.punctuate is True
    assert restored.numerals is True
    assert restored.interim_results is False
    assert restored.diarize is False
    assert restored.vad_events is True
    assert restored.endpointing == 400


def test_deepgram_tts_schema_includes_region():
    schema = DeepgramTTSConfiguration.model_json_schema()["properties"]
    assert schema["region"]["default"] == "us"
    assert _schema_enum_or_examples(schema["region"]) >= set(DEEPGRAM_REGIONS)
