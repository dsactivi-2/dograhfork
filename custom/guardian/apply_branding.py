#!/usr/bin/env python3
"""Apply custom/branding/docs_overlay.json onto docs/docs.json.

JSON cannot carry CUSTOM-SEAM comments, so branding lives in custom/ and
is written into the Mintlify config at image-build / post-merge time.
Re-run after every upstream merge.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OVERLAY_PATH = REPO_ROOT / "custom" / "branding" / "docs_overlay.json"
DOCS_JSON = REPO_ROOT / "docs" / "docs.json"


def apply(docs_path: Path = DOCS_JSON, overlay_path: Path = OVERLAY_PATH) -> dict:
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    docs = json.loads(docs_path.read_text(encoding="utf-8"))
    if overlay.get("name"):
        docs["name"] = overlay["name"]
    if overlay.get("banner"):
        docs["banner"] = overlay["banner"]
    support_href = (overlay.get("navbar") or {}).get("support_href")
    if support_href:
        navbar = docs.setdefault("navbar", {})
        links = navbar.setdefault("links", [])
        replaced = False
        for link in links:
            if link.get("label") == "Support":
                link["href"] = support_href
                replaced = True
                break
        if not replaced:
            links.insert(0, {"label": "Support", "href": support_href})
    docs_path.write_text(
        json.dumps(docs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return docs


def main() -> int:
    if not OVERLAY_PATH.is_file():
        print(f"missing overlay: {OVERLAY_PATH}", file=sys.stderr)
        return 2
    if not DOCS_JSON.is_file():
        print(f"missing docs.json: {DOCS_JSON}", file=sys.stderr)
        return 2
    apply()
    print(f"applied branding overlay → {DOCS_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
