from pydantic import TypeAdapter

from api.services.configuration.registry import (
    REGISTRY,
    ServiceProviders,
    ServiceType,
    STTConfig,
)
from custom.providers.deepgram_eu.schema import DeepgramEUSTTConfiguration


def test_us_deepgram_still_registered():
    keys = {getattr(k, "value", k) for k in REGISTRY[ServiceType.STT]}
    assert "deepgram" in keys
    assert "deepgram_eu" in keys
    assert (
        REGISTRY[ServiceType.STT][ServiceProviders.DEEPGRAM]
        is not DeepgramEUSTTConfiguration
    )


def test_deepgram_eu_schema_title():
    schema = DeepgramEUSTTConfiguration.model_json_schema()
    assert schema["title"] == "Deepgram EU"


def test_stt_union_accepts_both_providers():
    adapter = TypeAdapter(STTConfig)
    eu = adapter.validate_python(
        {
            "provider": "deepgram_eu",
            "api_key": "k",
            "model": "nova-3-general",
            "language": "de",
        }
    )
    assert eu.provider == ServiceProviders.DEEPGRAM_EU
    us = adapter.validate_python(
        {
            "provider": "deepgram",
            "api_key": "k",
            "model": "nova-3-general",
            "language": "de",
        }
    )
    assert us.provider == ServiceProviders.DEEPGRAM
