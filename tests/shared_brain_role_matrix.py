"""Live synthetic Shared Brain read/write matrix for all specialist identities.

Runs a bounded number of parallel requests. No model calls are made; all records
are synthetic and confined to the isolated integration-tests namespace.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ENDPOINT = os.getenv("SHARED_BRAIN_URL", "https://ydstbryiwiigzlqbrcpo.supabase.co/functions/v1/shared-brain")
OIDC_TOKEN = os.getenv("SHARED_BRAIN_GITHUB_OIDC_TOKEN", "")
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
        headers={"Content-Type": "application/json", "x-github-oidc-token": OIDC_TOKEN, "x-agent-id": identity},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                return response.status, json.loads(response.read(128_000).decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read(4096).decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                body = {}
            if exc.code not in {502, 503, 504} or attempt == 2:
                return exc.code, body
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == 2:
                return 599, {}
        time.sleep(0.25 * (2 ** attempt))


def check_role(role: str, nonce: str) -> tuple[str, bool, str]:
    identity = agent_id(role)
    slug = re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")
    memory_key = f"role-matrix:{nonce}:{slug}"
    marker = f"role-matrix:{nonce}:{role}"
    status, saved = post({
        "action": "remember", "project_key": "nexora", "namespace": NAMESPACE,
        "memory_key": memory_key, "source_agent": identity,
        "summary": marker, "content": {"synthetic": True, "role": role, "nonce": nonce},
        "tags": ["acceptance-test", "synthetic", "role-matrix"], "confidence": 1.0,
    }, identity)
    if status != 201 or saved.get("saved") is not True:
        return role, False, f"write failed (HTTP {status})"
    status, recalled = post({
        "action": "recall", "project_key": "nexora", "namespace": NAMESPACE,
        "query": marker, "limit": 5,
    }, identity)
    memories = recalled.get("memories")
    if status != 200 or not isinstance(memories, list) or not any(
        isinstance(row, dict) and row.get("memory_key") == memory_key for row in memories
    ):
        return role, False, f"read-after-write failed (HTTP {status})"
    return role, True, "ok"


def main() -> int:
    if not OIDC_TOKEN:
        print("FAIL: GitHub OIDC token is missing; role matrix cannot be skipped.")
        return 1
    nonce = secrets.token_hex(8)
    failures = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(check_role, role, nonce): role for role in ROLES}
        for future in as_completed(futures):
            role = futures[future]
            try:
                name, ok, reason = future.result()
            except Exception as exc:
                name, ok, reason = role, False, type(exc).__name__
            if not ok:
                failures.append((name, reason))
    if failures:
        for role, reason in sorted(failures):
            print(f"FAIL: {role}: {reason}")
        print(f"FAIL: {len(ROLES) - len(failures)}/{len(ROLES)} identities passed the live Shared Brain matrix.")
        return 1
    print(f"PASS: {len(ROLES)}/{len(ROLES)} identities passed synthetic Shared Brain write/read checks; no model calls made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
