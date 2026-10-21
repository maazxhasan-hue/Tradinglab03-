"""Authenticated live smoke test for the shared brain.

Uses only synthetic test data. Requires SHARED_BRAIN_AGENT_KEY in the environment.
Never prints credentials or memory content.
"""
from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.request

ENDPOINT = os.getenv(
    "SHARED_BRAIN_URL",
    "https://ydstbryiwiigzlqbrcpo.supabase.co/functions/v1/shared-brain",
)
KEY = os.getenv("SHARED_BRAIN_AGENT_KEY", "")
AGENT = "shared-brain-smoke-test"


def post(payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-agent-key": KEY,
            "x-agent-id": AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read(128_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read(4096).decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"error": "non-JSON response"}
        return exc.code, parsed


def main() -> int:
    if not KEY:
        print("SKIP: SHARED_BRAIN_AGENT_KEY is not configured.")
        return 0

    nonce = secrets.token_hex(8)
    memory_key = f"smoke-test:{nonce}"
    marker = f"shared-brain-smoke:{nonce}"
    status, saved = post({
        "action": "remember",
        "project_key": "nexora",
        "namespace": "integration-tests",
        "memory_key": memory_key,
        "source_agent": AGENT,
        "summary": marker,
        "content": {"marker": marker, "synthetic": True},
        "tags": ["smoke-test"],
        "confidence": 1.0,
    })
    if status != 201 or saved.get("saved") is not True:
        print(f"FAIL: authenticated write returned HTTP {status}; response keys={sorted(saved.keys())}")
        return 1

    status, recalled = post({
        "action": "recall",
        "project_key": "nexora",
        "namespace": "integration-tests",
        "query": marker,
        "limit": 5,
    })
    memories = recalled.get("memories")
    if status != 200 or not isinstance(memories, list) or not any(
        row.get("memory_key") == memory_key for row in memories if isinstance(row, dict)
    ):
        print(f"FAIL: read-after-write verification failed; HTTP {status}")
        return 1

    # Verify the public endpoint rejects an unauthenticated request.
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"action": "recall", "project_key": "nexora", "namespace": "integration-tests"}).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            unauth_status = response.status
    except urllib.error.HTTPError as exc:
        unauth_status = exc.code
    if unauth_status not in (401, 403):
        print(f"FAIL: unauthenticated request was not rejected (HTTP {unauth_status})")
        return 1

    print("PASS: authenticated write, cross-request recall, and unauthenticated rejection verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
