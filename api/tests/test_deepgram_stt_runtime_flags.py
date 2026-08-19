from types import SimpleNamespace
from unittest.mock import patch

from api.services.configuration.options import DEEPGRAM_NOVA_MODELS, DEEPGRAM_REGIONS
from api.services.configuration.registry import DeepgramSTTConfiguration, ServiceProviders
from api.services.pipecat.audio_config import AudioConfig
from api.services.pipecat.service_factory import create_stt_service, create_tts_service


def _audio_config() -> AudioConfig:
    return AudioConfig(
        transport_in_sample_rate=16000,
        transport_out_sample_rate=16000,
    )


def test_deepgram_stt_schema_exposes_region_and_nova_runtime_flags():
    schema = DeepgramSTTConfiguration.model_json_schema()["properties"]

    assert schema["region"]["default"] == "us"
    assert "us" in schema["region"]["enum"]
    assert "eu" in schema["region"]["enum"]
    assert set(DEEPGRAM_REGIONS) <= set(schema["region"]["enum"])

    for flag in (
        "smart_format",
        "punctuate",
        "interim_results",
        "diarize",
        "vad_events",
        "endpointing",
    ):
        visible = schema[flag].get("visible_for_models")
        assert visible is not None
        assert set(visible) == set(DEEPGRAM_NOVA_MODELS)

    assert schema["numerals"]["type"] == "boolean"
    assert "visible_for_models" not in schema["numerals"]
    assert schema["endpointing"]["default"] == 100
    assert schema["endpointing"]["minimum"] == 10
    assert schema["endpointing"]["maximum"] == 5000


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


def test_create_deepgram_nova_stt_uses_saved_region_and_flags():
    user_config = SimpleNamespace(
        stt=DeepgramSTTConfiguration(
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
    )

    with patch(
        "api.services.pipecat.service_factory.DeepgramSTTService"
    ) as mock_service:
        create_stt_service(user_config, _audio_config())

    kwargs = mock_service.call_args.kwargs
    assert kwargs["base_url"] == "api.eu.deepgram.com"
    settings = kwargs["settings"]
    assert settings.model == "nova-3-general"
    assert settings.language == "de"
    assert settings.smart_format is True
    assert settings.punctuate is True
    assert settings.numerals is True
    assert settings.interim_results is False
    assert settings.diarize is False
    assert settings.endpointing == 400
    assert settings.extra == {"vad_events": True}


def test_create_deepgram_nova_stt_defaults_match_previous_factory():
    """Legacy objects without the new attributes keep US + endpointing=100."""
    user_config = SimpleNamespace(
        stt=SimpleNamespace(
            provider=ServiceProviders.DEEPGRAM.value,
            api_key="test-key",
            model="nova-3-general",
            language="multi",
        )
    )

    with patch(
        "api.services.pipecat.service_factory.DeepgramSTTService"
    ) as mock_service:
        create_stt_service(user_config, _audio_config())

    kwargs = mock_service.call_args.kwargs
    assert kwargs["base_url"] == "api.deepgram.com"
    settings = kwargs["settings"]
    assert settings.endpointing == 100
    assert settings.model == "nova-3-general"
    assert settings.language == "multi"


def test_create_deepgram_flux_uses_region_and_skips_nova_listen_v1_flags():
    user_config = SimpleNamespace(
        stt=DeepgramSTTConfiguration(
            api_key="test-key",
            model="flux-general-multi",
            language="es",
            region="eu",
            smart_format=True,
            punctuate=True,
            interim_results=True,
            diarize=True,
            vad_events=True,
            endpointing=400,
            numerals=True,
        )
    )

    with patch(
        "api.services.pipecat.service_factory.DeepgramFluxSTTService"
    ) as mock_service:
        create_stt_service(user_config, _audio_config())

    kwargs = mock_service.call_args.kwargs
    assert kwargs["url"] == "wss://api.eu.deepgram.com/v2/listen"
    settings = kwargs["settings"]
    assert settings.model == "flux-general-multi"
    assert settings.numerals is True
    # Listen v1 flags must not be forwarded onto Flux settings.
    assert not hasattr(settings, "smart_format")
    assert not hasattr(settings, "endpointing")
    assert not hasattr(settings, "interim_results")

def test_create_deepgram_tts_uses_saved_region():
    user_config = SimpleNamespace(
        tts=SimpleNamespace(
            provider=ServiceProviders.DEEPGRAM.value,
            api_key="test-key",
            voice="aura-2-helena-en",
            region="eu",
        )
    )

    with patch(
        "api.services.pipecat.service_factory.DeepgramTTSService"
    ) as mock_service:
        create_tts_service(user_config, _audio_config())

    kwargs = mock_service.call_args.kwargs
    assert kwargs["base_url"] == "wss://api.eu.deepgram.com"
