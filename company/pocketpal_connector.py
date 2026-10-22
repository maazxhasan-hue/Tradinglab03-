"""Optional client for a private OpenAI-compatible local inference endpoint.

Important: PocketPal AI's official Android app currently runs inference in-process
and documents no supported HTTP server/API. This module does NOT connect to the
PocketPal app directly. It can connect to a separate local server (for example,
llama.cpp server running on the phone) that uses the same downloaded GGUF model.

It is intentionally opt-in and is not imported by the trading runtime.
"""
from __future__ import annotations

import ipaddress
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class LocalModelError(RuntimeError):
    """Safe-to-display local model connection or response error."""


def _validated_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Local model URL must be plain HTTP on a trusted private network, without credentials.")
    host = parsed.hostname.lower()
    if host == "localhost":
        return value
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("Use localhost or a literal private/LAN IP address; DNS hostnames are not allowed.") from exc
    if not (address.is_private or address.is_loopback or address.is_link_local):
        raise ValueError("Local model URL must use a private, loopback, or link-local IP address.")
    return value


def chat_completion(
    messages: list[dict[str, str]],
    *,
    base_url: str | None = None,
    model: str | None = None,
    timeout_seconds: float = 30.0,
    max_tokens: int = 512,
) -> dict:
    """Call an OpenAI-compatible private local model server.

    Environment:
      TRADINGLAB03_LOCAL_MODEL_URL (required; e.g. http://192.168.1.25:8080)
      TRADINGLAB03_LOCAL_MODEL_NAME (default: local-model)
      TRADINGLAB03_LOCAL_MODEL_TOKEN (optional bearer token)

    This client deliberately supports text-only chat completions, not tools,
    file access, shell commands, deployment, or trading actions.
    """
    endpoint = _validated_base_url(
        base_url or os.environ.get("TRADINGLAB03_LOCAL_MODEL_URL", "")
    )
    model_name = (model or os.environ.get("TRADINGLAB03_LOCAL_MODEL_NAME", "local-model")).strip()
    if not model_name:
        raise ValueError("Model name must not be empty.")
    if not isinstance(messages, list) or not messages or any(
        not isinstance(message, dict)
        or message.get("role") not in {"system", "user", "assistant"}
        or not isinstance(message.get("content"), str)
        for message in messages
    ):
        raise ValueError("messages must be a non-empty list of system/user/assistant text messages.")
    if not 1 <= int(max_tokens) <= 2048:
        raise ValueError("max_tokens must be between 1 and 2048.")
    if not 1 <= float(timeout_seconds) <= 120:
        raise ValueError("timeout_seconds must be between 1 and 120.")

    payload = json.dumps({
        "model": model_name,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": int(max_tokens),
        "stream": False,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("TRADINGLAB03_LOCAL_MODEL_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        endpoint + "/v1/chat/completions", data=payload, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_seconds)) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not return response bodies; a local server could echo prompts or secrets.
        raise LocalModelError(f"Local model server returned HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise LocalModelError("Local model server is unreachable or timed out.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise LocalModelError("Local model server returned invalid JSON.") from None

    try:
        text = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise LocalModelError("Local model response did not match the chat-completions format.") from None
    if not isinstance(text, str):
        raise LocalModelError("Local model returned a non-text response.")
    return {"model": model_name, "content": text, "provider": "private_local"}
