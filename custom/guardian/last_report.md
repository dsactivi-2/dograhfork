Datum: 2026-08-18
Agent: Grok Build / Dograh Guardian
Aktion: implement
Upstream SHA vorher/nachher: 689ca048bb0ab03183d6904b6c6eb6a405084dd0 (unverändert)
custom/ intakt: ja
Seams vorhanden: ja (registry, factory, check_validity, Dockerfile)
Defaults-Endpoint deepgram_eu: nicht geprüft (kein laufendes Dograh-API in dieser Session)
Fish Audio Schema/Factory: ja, in custom/providers/fish_audio/
Banner overlay: ja, custom/branding/docs_overlay.json → docs/docs.json
Healthcheck: Exit 0 (Registry-Smoke übersprungen — kein Dograh-venv)
Nächster menschlicher Schritt: Branch `custom` als Default setzen, VPS im **build**-Modus auf diesen Branch zeigen, `docker compose --profile remote up -d --build`
