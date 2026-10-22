# PocketPal / Android local-model connector (experimental)

## Official PocketPal interface inspection

The official PocketPal repository is https://github.com/a-ghorbani/pocketpal-ai. Its README describes an on-device React Native application using `llama.rn`/llama.cpp, GGUF models, Pals, and in-app Talents. It does **not** document a supported HTTP/OpenAI-compatible server endpoint. This repository therefore does not claim to connect to PocketPal's in-memory model session. Do not scrape app storage, inject into the app, or expose undocumented interfaces.

## Recommended Android server option

For a real HTTP endpoint on Android, evaluate [PocketLLM](https://github.com/Kimi-syl/PocketLLM), whose project README documents an API-key-protected OpenAI-compatible server with `GET /v1/models` and `POST /v1/chat/completions`. It is a separate app/project, not a PocketPal plugin. Review its permissions, source, model support and current release before installing. Another option is building/running llama.cpp's server under Termux, following the official [llama.cpp Android guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md).

On the Realme 10 Pro (8 GB RAM), begin with a small quantized 1–2B GGUF model and a short context. Android, the model runtime and other apps share RAM; sustained inference may heat the phone, drain the battery or be suspended in the background.

## What this repository includes

`company/pocketpal_connector.py` is an optional, isolated client for a **separate private OpenAI-compatible inference server**. It is not imported by the existing TradingLab03 or trading-agent runtime and does not activate itself.

Safety properties:
- Text-only chat messages; no tools, shell, file writes, deployments, or trading actions.
- Endpoint must use HTTP on loopback, link-local, or a private IP; public IPs and DNS hostnames are rejected.
- Optional bearer token; response errors are sanitized to avoid echoing prompts or credentials.
- Request token count and timeout are bounded.
- No changes to live trading services or existing agent workflows.

## Environment

Configure these only in the process that should call the local model:

- `TRADINGLAB03_LOCAL_MODEL_URL`: required private endpoint, e.g. `http://192.168.1.25:8080`
- `TRADINGLAB03_LOCAL_MODEL_NAME`: optional model identifier, default `local-model`
- `TRADINGLAB03_LOCAL_MODEL_TOKEN`: optional bearer token configured on the server; strongly recommended for LAN access

Example:

```python
from company.pocketpal_connector import chat_completion

reply = chat_completion([
    {"role": "system", "content": "Explain errors; never execute commands."},
    {"role": "user", "content": "Summarize this sanitized log: ..."},
])
print(reply["content"])
```

The server must implement `POST /v1/chat/completions` and return `choices[0].message.content`.

## Secure networking

An Android app's `localhost` is the phone itself. A cloud GitHub Actions runner or Azure VM cannot reach `127.0.0.1` on the phone. For remote access, use a private overlay network with authenticated access and bind the server only to the overlay/LAN interface. Do **not** expose the model port publicly or use an unauthenticated public tunnel. The client rejects public IPs and DNS names, but that is only one layer of defense; network ACLs and server authentication are still required.

Android may suspend background work, so the phone is an optional inference worker, not a reliable always-on production backend. PocketPal and a separate server would run separate model processes and consume separate RAM if both load the same model.

## Validation

Run:

```sh
python -m unittest tests.test_pocketpal_connector -v
```

Tests cover request formatting, private-address restrictions, rejected roles, and error sanitization. They do not prove a real Android server is available. Keep integration opt-in until the phone endpoint is configured and a live end-to-end test succeeds.
