# VoiceEU Guardian

This branch (`Guardian-Dograh`) is Dograh **plus** the VoiceEU overlay.

- Overlay and providers: [`custom/`](custom/)
- Deploy + troubleshooting: [`custom/DEPLOY.md`](custom/DEPLOY.md)
- Start: `bash custom/scripts/deploy.sh` (laptop) or `bash custom/scripts/deploy.sh remote` (VPS)
- Diagnose: `bash custom/scripts/diagnose.sh`

Guardian talks to Dograh at `http://api:8000/api/v1/health` on the same Docker network.
