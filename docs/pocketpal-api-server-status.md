# PocketPal API server: current status and safe integration path

**Checked 2026-10-22.** Keep the installed PocketPal app and Gemma model; do not uninstall them.

## Finding

The PocketPal main branch/released app does not yet document an enabled local API server in the UI. However, the official repository has an **open draft proof-of-concept pull request**:
https://github.com/a-ghorbani/pocketpal-ai/pull/990

The POC describes:
- Settings → Local API server card
- `GET /v1/models` and `POST /v1/chat/completions`
- Server off by default; loopback-only by default; optional LAN access and optional API key
- Requests use the currently loaded local model and share a generation queue with in-app chat
- Tools, image requests, and some advanced request features are rejected

This is a draft, not a released feature guaranteed to be present in the user's installed app. Do not assume the current Play Store build contains it.

## Safety and next steps

1. Continue using the installed PocketPal + Gemma for local chat.
2. Wait for the official PR to be reviewed/merged and a release containing the feature, **or** build a clearly labelled test APK from the PR branch only if a trusted build environment is available.
3. If using a test APK, verify the signing/source before installing. A debug-signed build may not update the store version in place; back up chat history before any replacement and never uninstall the existing app without a backup.
4. First test loopback access from the phone. Then, only if required, opt into LAN access and set a strong API key. Never expose the port to the public internet or an unauthenticated tunnel.
5. Configure the existing TradingLab03 local connector only after a harmless end-to-end API request succeeds. The connector requires a private IP literal and an OpenAI-compatible response. Review its private-network validation against the chosen VPN/overlay address before use.
6. Keep integration opt-in and text-only. Do not enable it inside the live trading process until separately validated.

## Existing TradingLab03 connector

`company/pocketpal_connector.py` is an isolated optional client. It is not imported by the live trading runtime and does not enable itself. It can call the PocketPal API only if the API server feature is actually available and running.

The existing trading agent/service must not be restarted, modified, or reconfigured as part of this phone setup.
