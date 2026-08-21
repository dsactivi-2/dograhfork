import pytest

from custom.processors.emotion_text_filter import EmotionTextFilter


@pytest.mark.asyncio
async def test_injects_default_tag_when_missing():
    f = EmotionTextFilter(default_tag="friendly", enabled=True)
    out = await f.filter("Dobar dan, kako ste?")
    assert out == "[friendly] Dobar dan, kako ste?"


@pytest.mark.asyncio
async def test_preserves_existing_tag():
    f = EmotionTextFilter(default_tag="friendly", enabled=True)
    src = "[empathetic] Razumijem vašu frustraciju."
    assert await f.filter(src) == src


@pytest.mark.asyncio
async def test_preserves_freeform_tag():
    f = EmotionTextFilter(default_tag="friendly", enabled=True)
    src = "[speaking softly] Molim vas, sačekajte."
    assert await f.filter(src) == src


@pytest.mark.asyncio
async def test_disabled_is_noop():
    f = EmotionTextFilter(default_tag="friendly", enabled=False)
    src = "Dobar dan"
    assert await f.filter(src) == src


@pytest.mark.asyncio
async def test_skips_whitespace_only():
    f = EmotionTextFilter(default_tag="calm", enabled=True)
    assert await f.filter("   ") == "   "
    assert await f.filter("") == ""


@pytest.mark.asyncio
async def test_update_settings_changes_tag():
    f = EmotionTextFilter(default_tag="friendly", enabled=True)
    await f.update_settings({"default_tag": "empathetic"})
    out = await f.filter("Hvala")
    assert out == "[empathetic] Hvala"
