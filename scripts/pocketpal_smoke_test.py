#!/usr/bin/env python3
"""Safe, text-only smoke test for a private OpenAI-compatible local model API.

This script does not modify configuration, start services, or call trading tools.
It checks GET /v1/models and sends one harmless chat-completion request.
The endpoint must be loopback/private/link-local HTTP; public IPs and DNS names
are rejected by the same validator used by the optional connector.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from company.pocketpal_connector import (
    LocalModelError,
    _validated_base_url,
    chat_completion,
)


def main() -> int:
    raw_url = os.environ.get("TRADINGLAB03_LOCAL_MODEL_URL", "").strip()
    if not raw_url:
        print("FAIL: set TRADINGLAB03_LOCAL_MODEL_URL to the private server URL.")
        return 2

    try:
        base_url = _validated_base_url(raw_url)
    except ValueError as exc:
        print(f"FAIL: endpoint rejected: {exc}")
        return 2

    headers = {}
    token = os.environ.get("TRADINGLAB03_LOCAL_MODEL_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        base_url + "/v1/models", headers=headers, method="GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            models_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"FAIL: model-list endpoint returned HTTP {exc.code}; check server and API key.")
        return 1
    except (urllib.error.URLError, TimeoutError, OSError):
        print("FAIL: server unreachable or timed out; check phone server and private network.")
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("FAIL: /v1/models returned invalid JSON.")
        return 1

    models = models_payload.get("data") if isinstance(models_payload, dict) else None
    if not isinstance(models, list) or not models:
        print("FAIL: /v1/models did not return a non-empty data list.")
        return 1
    model_id = models[0].get("id") if isinstance(models[0], dict) else None
    if not isinstance(model_id, str) or not model_id.strip():
        print("FAIL: first model entry has no usable id.")
        return 1

    try:
        result = chat_completion(
            [{"role": "user", "content": "Reply with exactly: POCKETPAL_CONNECTION_OK"}],
            base_url=base_url,
            model=model_id,
            timeout_seconds=60,
            max_tokens=32,
        )
    except (ValueError, LocalModelError) as exc:
        print(f"FAIL: chat-completion check failed: {exc}")
        return 1

    if not result.get("content", "").strip():
        print("FAIL: server returned an empty text completion.")
        return 1

    # Never print the API key or the model's full response; only a short success marker.
    print("PASS: /v1/models returned at least one model.")
    print(f"PASS: text chat completion succeeded (model id: {model_id[:80]}).")
    print("PASS: connector remained text-only; no tools or trading actions were called.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
