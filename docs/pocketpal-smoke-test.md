# PocketPal local API smoke test

This is a pre-integration check for an OpenAI-compatible local server. It does not enable the connector in TradingLab03 and does not touch the live trading service.

## Preconditions

- PocketPal has an official/reviewed build that actually includes **Settings → Local API server**. The upstream implementation may still be a draft; do not assume it exists in the installed Play Store build.
- Load the local model in PocketPal and start the server with API-key authentication enabled.
- Keep the listener loopback-only for same-device testing. For phone-to-VM testing, use a private authenticated network path and the phone's private/overlay IP; never expose the port publicly.
- Set the URL and key only in the shell/process that runs the test. Do not commit secrets or paste them into chat.

## Run

From the repository root:

```bash
export TRADINGLAB03_LOCAL_MODEL_URL='http://PRIVATE_PHONE_IP:8080'
read -s -p 'PocketPal API key: ' TRADINGLAB03_LOCAL_MODEL_TOKEN; export TRADINGLAB03_LOCAL_MODEL_TOKEN; echo
python scripts/pocketpal_smoke_test.py
unset TRADINGLAB03_LOCAL_MODEL_TOKEN
```

For same-phone testing, use `http://127.0.0.1:8080`. That address only refers to the phone when the script runs on the phone; it refers to the VM if run on Azure.

Expected output is three `PASS` lines. A failure is diagnostic only; do not enable live integration to bypass it.

## Scope and safety

- Requests `GET /v1/models` and one harmless text-only `POST /v1/chat/completions`.
- Uses the existing connector's endpoint validator, timeout bounds, and sanitized HTTP errors.
- Does not execute tools, shell commands, file changes, deployments, or trades.
- Does not change environment variables permanently, edit service files, or restart any service.
- A successful smoke test proves only that the API responds from the machine running the test. It does not by itself prove production reliability or authorize use in the live trading runtime.
