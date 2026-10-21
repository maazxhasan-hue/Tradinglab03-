"""Live synthetic shared-brain read/write matrix for every specialist identity.

No model calls are made. All writes use the isolated integration-tests namespace.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import urllib.error
import urllib.request

ENDPOINT = os.getenv("SHARED_BRAIN_URL", "https://ydstbryiwiigzlqbrcpo.supabase.co/functions/v1/shared-brain")
KEY = os.getenv("SHARED_BRAIN_AGENT_KEY", "")
ROLES = [
    "CEO Strategy", "Market Intelligence", "Lead Discovery", "Sales Qualification",
    "Proposal & Pricing", "Client Success", "Brand & Positioning", "Content Strategy",
    "Copywriting", "Social & Community", "SEO & Website Growth", "Growth Analytics",
    "Product Manager", "UX/UI Design", "Frontend Development", "Backend & Integrations",
    "Testing & QA", "Security & Privacy", "Release & DevOps", "Documentation",
    "Project Operations", "Finance & Revenue", "Policy & Compliance", "Knowledge & Memory",
    "Workflow Automation", "Customer Support", "Experiment & Learning",
    "Trading Systems Monitor", "Reverse Writing Agent", "Studio Agent",
]
NAMESPACE = "integration-tests"


def agent_id(role: str) -> str:
    return "nexora-" + re.sub(r"[^a-zA-Z0-9._:-]", "-", role.lower())[:80]


def post(payload: dict, identity: str) -> tuple[int, dict]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "x-agent-key": KEY, "x-agent-id": identity},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read(128_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read(4096).decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            body = {}
        return exc.code, body


def main() -> int:
    if not KEY:
        print("FAIL: SHARED_BRAIN_AGENT_KEY is missing; role matrix cannot be skipped.")
        return 1
    nonce = secrets.token_hex(8)
    passed = 0
    for role in ROLES:
        identity = agent_id(role)
        memory_key = f"role-matrix:{nonce}:{re.sub(r'[^a-z0-9]+', '-', role.lower()).strip('-')}"
        marker = f"role-matrix:{nonce}:{role}"
        status, saved = post({
            "action": "remember", "project_key": "nexora", "namespace": NAMESPACE,
            "memory_key": memory_key, "source_agent": identity,
            "summary": marker, "content": {"synthetic": True, "role": role, "nonce": nonce},
            "tags": ["acceptance-test", "synthetic", "role-matrix"], "confidence": 1.0,
        }, identity)
        if status != 201 or saved.get("saved") is not True:
            print(f"FAIL: {role} write failed (HTTP {status}).")
            return 1
        status, recalled = post({
            "action": "recall", "project_key": "nexora", "namespace": NAMESPACE,
            "query": marker, "limit": 5,
        }, identity)
        memories = recalled.get("memories")
        if status != 200 or not isinstance(memories, list) or not any(
            isinstance(row, dict) and row.get("memory_key") == memory_key for row in memories
        ):
            print(f"FAIL: {role} read-after-write failed (HTTP {status}).")
            return 1
        passed += 1
    print(f"PASS: {passed}/{len(ROLES)} role identities completed isolated synthetic Shared Brain write/read checks; no model calls made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
