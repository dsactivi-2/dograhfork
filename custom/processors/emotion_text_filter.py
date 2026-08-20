"""Inject Fish Audio S2 emotion tags before TTS when the LLM omits them.

Fish S2 / S2.1 reads free-form [bracket] cues in the spoken text. The agent
prompt is supposed to emit them; this filter is a safety net so every
aggregated utterance still gets a default tag when none is present.

Applies after sentence aggregation inside Pipecat TTSService.text_filters.
Does not touch chunks that already start with a [tag].
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

from pipecat.utils.text.base_text_filter import BaseTextFilter

# Leading Fish S2 emotion / direction tag, e.g. [friendly] or [slightly sad]
_LEADING_TAG = re.compile(r"^\s*\[[^\]]+\]")

_ALLOWED_DEFAULTS = frozenset(
    {
        "friendly",
        "empathetic",
        "confident",
        "calm",
        "sad",
        "happy",
        "excited",
        "nervous",
        "neutral",
    }
)


def _normalize_tag_name(raw: str | None, fallback: str = "friendly") -> str:
    name = (raw or fallback).strip().lower().strip("[]")
    if not name:
        return fallback
    # Allow free-form S2 tags, but prefer known short names when empty junk slips in
    if len(name) > 64:
        return fallback
    return name


class EmotionTextFilter(BaseTextFilter):
    """Prefix text with [emotion] when no leading Fish tag is present.

    Args:
        default_tag: Tag name without brackets (e.g. ``"friendly"``).
            Overridden by env ``FISH_EMOTION_DEFAULT_TAG`` when set.
        enabled: When False, filter is a no-op. Env ``FISH_EMOTION_INJECT=0``
            also disables.
    """

    def __init(
        self,
        *,
        default_tag: str | None = None,
        enabled: bool | None = None,
    ):
        env_enabled = os.environ.get("FISH_EMOTION_INJECT", "1").strip().lower()
        if enabled is None:
            enabled = env_enabled not in {"0", "false", "no", "off"}
        env_tag = os.environ.get("FISH_EMOTION_DEFAULT_TAG")
        tag = _normalize_tag_name(env_tag if env_tag else default_tag, "friendly")
        self._default_tag = tag
        self._enabled = bool(enabled)

    @property
    def default_tag(self) -> str:
        return self._default_tag

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def update_settings(self, settings: Mapping[str, Any]) -> None:
        if "enabled" in settings:
            self._enabled = bool(settings["enabled"])
        if "default_tag" in settings:
            self._default_tag = _normalize_tag_name(
                str(settings["default_tag"]), self._default_tag
            )

    async def filter(self, text: str) -> str:
        if not self._enabled or not text:
            return text
        if not text.strip():
            return text
        if _LEADING_TAG.match(text):
            return text
        # Avoid tagging pure punctuation / whitespace fragments
        if not any(ch.isalnum() for ch in text):
            return text
        return f"[{self._default_tag}] {text.lstrip()}"

    async def handle_interruption(self) -> None:
        return

    async def reset_interruption(self) -> None:
        return
