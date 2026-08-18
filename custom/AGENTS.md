# custom/ — Guardian contract

Read `dograh-guardian/RUNBOOK.md` and `dograh-guardian/AGENTS.md` first.

- New providers go in `custom/providers/<id>/`.
- Core files may only receive `CUSTOM-SEAM` lines listed in `seams/SEAM_MAP.md`.
- Do not patch `DeepgramSTTConfiguration` / `DeepgramTTSConfiguration`.
- Do not copy upstream files into this tree to “maintain our version”.
- Banner / docs name live in `branding/docs_overlay.json`. Re-apply after merge.
