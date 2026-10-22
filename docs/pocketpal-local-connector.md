# PocketPal / Android local-model connector (experimental)

## Official interface inspection

The official PocketPal repository is https://github.com/a-ghorbani/pocketpal-ai. Its README describes an on-device React Native application using `llama.rn`/llama.cpp, GGUF models, Pals, and in-app Talents. The official README does **not** document an HTTP server, OpenAI-compatible API, or supported remote inference endpoint.

Therefore this repository does not pretend that TradingLab03 can call the PocketPal app directly. Do not scrape PocketPal's internal app storage, inject into the app, or expose an undocumented debug interface.

## What is included

`company/pocketpal_connector.py` is an optional, isolated client for a **separate private OpenAI-compatible inference server**. It can be used with a local llama.cpp server running the same compatible GGUF model, including on Android/Termux if the device can run the server. This is not a PocketPal app plugin and does not share PocketPal's in-memory model session.

Safety properties:
- Not imported by the existing TradingLab03 or trading-agent runtime.
- No auto-activation and no changes to live services or GitHub Actions workflows.
- Only text chat messages are accepted; there are no tools, shell, file-write, deployment, or trading actions.
- Endpoint must be HTTP on loopback, link-local, or a private IP; public IPs and DNS hostnames are rejected.
- Optional bearer token is supported; server errors are sanitized to avoid echoing prompts or credentials.
- Request token count and timeout are bounded.

## Environment

Configure these only in the process that should call the local model:

- `TRADINGLAB03_LOCAL_MODEL_URL`: required private endpoint, e.g. `http://192.168.1.25:8080`
- `TRADINGLAB03_LOCAL_MODEL_NAME`: optional model identifier, default `local-model`
- `TRADINGLAB03_LOCAL_MODEL_TOKEN`: optional bearer token configured on the server

Example (after a compatible private server has been started and secured):

```python
from company.pocketpal_connector import chat_completion

reply = chat_completion([
    {"role": "system", "content": "Explain errors; never execute commands."},
    {"role": "user", "content": "Summarize this sanitized log: ..."},
])
print(reply["content"])
```

The endpoint must implement `POST /v1/chat/completions` and return the OpenAI-compatible `choices[0].message.content` field.

## Android connectivity caveat

An Android app's `localhost` is the phone itself. A cloud GitHub Actions runner or Azure VM cannot reach `127.0.0.1` on the phone. For remote access, use a private overlay network with authenticated access and a server bound only to the overlay/LAN interface. Do not expose the model port publicly or add an unauthenticated public tunnel. Android may suspend background work; this is not suitable as the only production inference backend.

PocketPal currently documents on-device chat, not a server endpoint. If the goal is to reuse the exact model file, run a separate compatible llama.cpp server with that GGUF file instead; PocketPal and that server will use separate model processes and consume separate RAM.

## Validation

Run:

```sh
python -m unittest tests.test_pocketpal_connector -v
```

This tests request formatting, private-address restrictions, rejected roles, and error sanitization. It does not prove that a real Android model server is available. Integration remains opt-in until a server is separately configured and a live end-to-end test succeeds.
