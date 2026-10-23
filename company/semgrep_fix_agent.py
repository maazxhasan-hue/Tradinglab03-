"""Generate a bounded, review-first remediation patch from Semgrep findings.

This helper never commits or deploys changes. The caller must validate the patch,
run tests, and open a pull request for human review.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PREFIXES = ("company/", "harvey-worker/", "tests/")
ALLOWED_FILES = {"private_hq_server.py"}
MAX_CONTEXT_CHARS = 36_000


def validated_model_name(value: str) -> str:
    """Keep model identifiers from changing the fixed provider request path."""
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", value):
        raise ValueError("Model name contains unsupported characters.")
    return value


def post_json_https(host: str, path: str, headers: dict[str, str], payload: dict) -> dict:
    """POST JSON over verified TLS to a hard-coded provider host."""
    if host not in {"generativelanguage.googleapis.com", "api.openai.com"}:
        raise ValueError("Provider host is not allowlisted.")
    if not path.startswith("/") or path.startswith("//") or "\\\\" in path:
        raise ValueError("Provider request path is invalid.")
    connection = http.client.HTTPSConnection(host, timeout=90)
    try:
        connection.request(
            "POST", path, body=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json", "Accept": "application/json"},
        )
        response = connection.getresponse()
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise RuntimeError("Provider response exceeded the size limit.")
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Provider returned HTTP {response.status}.")
        return json.loads(raw.decode("utf-8"))
    finally:
        connection.close()

