# Free local AI on Android — quick setup

This uses local inference, so model responses do not consume paid API tokens. It is not literally unlimited: the phone's RAM, battery, heat, and background limits still apply.

## 1. Install the app

Install PocketLLM from its official GitHub Releases page:
https://github.com/Kimi-syl/PocketLLM/releases/latest

Review the release and permissions before installing. This is a separate project from PocketPal.

## 2. Download and load a small model

In PocketLLM:
1. Open **Models**.
2. Download a small quantized GGUF model (start around 1B–2B parameters).
3. Load it and test a short prompt.

Keep the phone cool and plugged in during downloads/inference if convenient. Avoid starting with large models.

## 3. Enable an authenticated API

1. Open **Server** and start the server.
2. Open **Keys** and create an API key.
3. Keep **Require API key** enabled.
4. Do not post or send the key to anyone.
5. Do not forward port 8080 to the public internet.

PocketLLM documents an OpenAI-compatible API:
- `GET /v1/models`
- `POST /v1/chat/completions`

On the phone itself, its local endpoint is typically `http://127.0.0.1:8080/v1`. This loopback address cannot be used by an Azure VM because it points to the VM itself when used there.

## 4. Connect it to TradingLab03 safely

The repository already contains an isolated optional client:
https://github.com/maazxhasan-hue/Tradinglab03-/blob/main/company/pocketpal_connector.py

Setup guide:
https://github.com/maazxhasan-hue/Tradinglab03-/blob/main/docs/pocketpal-local-connector.md

**Important:** the client is not enabled by default and is not imported into the trading runtime. Do not enable it in a live trading process until a separate end-to-end test passes. The current VM has limited memory, and the existing trading-agent service must not be disrupted.

For a phone-to-VM connection, first establish a private authenticated network path (for example, a properly configured private overlay VPN on both devices). Then verify the overlay address is accepted by the client's IP validation and that the API key is required by the server. Some overlay address ranges may not be accepted by Python's `ipaddress.is_private`; do not work around this by exposing the server publicly. If the address is rejected, update the validator with an explicit, tested allowlist for the chosen private overlay before enabling the integration.

## 5. Verify before integration

- Confirm the model answers in the app.
- Confirm the server is running and API-key protection is on.
- Test `/v1/models` from a trusted client without sharing the API key.
- Test a harmless chat completion using a secret stored only on the client machine.
- Run `python -m unittest tests.test_pocketpal_connector -v` in the repository.
- Keep the connector opt-in until the live test succeeds.

## What is and isn't done

The repository connector and its automated tests exist. The Android app installation, model download, API-key creation, private network setup, and live phone-to-VM request require actions on the phone/network and have not been represented as completed. No existing trading service should be stopped, restarted, or reconfigured for this setup.
