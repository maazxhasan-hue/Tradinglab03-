# Gemma + ChatGPT Connector (Android prototype)

This is a separate Android app prototype for calling a PocketPal OpenAI-compatible local endpoint and optionally asking OpenAI's API for a complementary response. It is isolated from TradingLab03's live trading runtime.

## Important
- This does not make ChatGPT itself connect directly to PocketPal. It connects your own app to two separate endpoints.
- PocketPal must have its experimental local API server enabled. The API-server feature is currently in a draft upstream PR, not a guaranteed Play Store feature.
- OpenAI API calls require a separate API key and are billed separately from a ChatGPT subscription.
- Do not enable LAN access without a strong bearer token and a trusted network.
- This prototype has no tool execution, file access, shell, or trading functions.

## Build
Requires JDK 17 and Android SDK 35. Run `gradle assembleDebug`. The included GitHub Actions workflow builds a debug APK artifact.

## Safety
The connector does not store keys persistently. Use HTTPS for cloud endpoints and loopback HTTP only for PocketPal. Keep the live trading agent untouched while validating this prototype.
