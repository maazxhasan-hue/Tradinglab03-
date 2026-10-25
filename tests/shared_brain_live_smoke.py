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
OIDC_TOKEN = os.getenv("SHARED_BRAIN_GITHUB_OIDC_TOKEN", "")
AGENT = "shared-brain-smoke-test"


def post(payload: dict, agent: str = AGENT) -> tuple[int, dict]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-github-oidc-token": OIDC_TOKEN,
            "x-agent-id": agent,
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
    if not OIDC_TOKEN:
        print("FAIL: GitHub OIDC token is not configured; live shared-brain verification cannot be skipped.")
        return 1

    nonce = secrets.token_hex(8)
    memory_key = f"smoke-test:{nonce}"
    marker = f"shared-brain-smoke:{nonce}"
    writer_agent = "shared-brain-smoke-writer"
    reader_agent = "shared-brain-smoke-reader"
    status, saved = post({
        "action": "remember",
        "project_key": "nexora",
        "namespace": "integration-tests",
        "memory_key": memory_key,
        "source_agent": writer_agent,
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
    }, agent=reader_agent)
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

    print("PASS: writer-to-different-agent recall, authenticated write, and unauthenticated rejection verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
