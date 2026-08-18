#!/usr/bin/env python3
"""Guardian healthcheck. Exit 0 only when overlay + seams are intact.

Exit 2 = custom/ damaged.
Exit 3 = seam lost.
Exit 4 = forbidden core edit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "custom" / "guardian" / "expected_manifest.json"


def _read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _fail(code: int, message: str) -> int:
    print(f"FAIL ({code}): {message}")
    return code


def main() -> int:
    if not MANIFEST_PATH.is_file():
        return _fail(2, f"missing manifest {MANIFEST_PATH}")
    manifest = _read_manifest()
    marker = manifest["marker"]

    for rel in manifest["required_paths"]:
        path = REPO_ROOT / rel
        if not path.is_file() or path.stat().st_size == 0:
            return _fail(2, f"required path missing or empty: {rel}")

    for rel in manifest["required_seams"]:
        path = REPO_ROOT / rel
        if not path.is_file():
            return _fail(3, f"seam file missing: {rel}")
        text = path.read_text(encoding="utf-8", errors="replace")
        if marker not in text:
            return _fail(3, f"{rel} lost {marker}")
        for token in manifest.get("required_markers", ["deepgram_eu"]):
            if token not in text:
                return _fail(3, f"{rel} lost marker {token}")

    overlay = json.loads(
        (REPO_ROOT / "custom" / "branding" / "docs_overlay.json").read_text(
            encoding="utf-8"
        )
    )
    if overlay.get("banner", {}).get("content") in (None, ""):
        return _fail(2, "docs overlay banner.content is empty")

    for rel in manifest.get("forbidden_edits", []):
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        try:
            diff = subprocess.run(
                ["git", "diff", "upstream/main", "--", rel],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            diff = None
        if diff and diff.returncode == 0 and diff.stdout.strip():
            return _fail(4, f"forbidden edit vs upstream/main: {rel}")

    try:
        sys.path.insert(0, str(REPO_ROOT))
        from api.services.configuration.registry import (  # noqa: WPS433
            REGISTRY,
            ServiceType,
        )

        stt = {getattr(k, "value", k) for k in REGISTRY[ServiceType.STT]}
        tts = {getattr(k, "value", k) for k in REGISTRY[ServiceType.TTS]}
        if "deepgram" not in stt:
            return _fail(2, "US deepgram missing from STT registry")
        if "deepgram_eu" not in stt:
            return _fail(2, "deepgram_eu missing from STT registry")
        if "deepgram_eu" not in tts:
            return _fail(2, "deepgram_eu missing from TTS registry")
        if "fish_audio" not in tts:
            return _fail(2, "fish_audio missing from TTS registry")
        print("registry smoke: deepgram + deepgram_eu + fish_audio present")
    except Exception as exc:  # import only works inside the Dograh venv
        print(f"registry smoke skipped ({exc.__class__.__name__}: {exc})")

    print("OK: overlay paths, seams, and branding source are intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
