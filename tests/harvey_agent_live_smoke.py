"""One-shot live smoke test for the production specialist API.

This creates one synthetic internal task. It never contacts people, publishes
content, trades, purchases anything, or performs other external actions.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def main() -> int:
    api_key = os.getenv("HARVEY_API_KEY")
    if not api_key:
        print("FAIL: HARVEY_API_KEY GitHub secret is missing; live execution was not tested.")
        return 1

    base = os.getenv("HARVEY_WORKER_URL", "https://nexora-harvey-worker.onrender.com").rstrip("/")
    payload = {
        "role": "Knowledge & Memory",
        "goal": (
            "Synthetic internal connectivity test only. Include the exact marker "
            "NEXORA_AGENT_EXECUTION_OK in the deliverable. Do not use external tools "
            "or perform any external action."
        ),
        "context": (
            "Automated smoke test only; no client data. Do not contact anyone, publish "
            "content, send messages, trade, purchase anything, or change settings."
        ),
        "constraints": (
            "Return a brief structured result. The deliverable must include "
            "NEXORA_AGENT_EXECUTION_OK. Do not perform external actions."
        ),
    }
    request = urllib.request.Request(
        base + "/agents/run",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "Nexora-Agent-Live-Smoke/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=150) as response:
            if response.status != 200:
                print(f"FAIL: specialist endpoint returned HTTP {response.status}.")
                return 1
            data = json.loads(response.read(512_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"FAIL: specialist endpoint returned HTTP {exc.code}; response body withheld.")
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"FAIL: specialist request could not complete ({type(exc).__name__}).")
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("FAIL: specialist endpoint returned invalid JSON.")
        return 1

    if not isinstance(data, dict):
        print("FAIL: specialist endpoint returned a non-object JSON response.")
        return 1

    brain = data.get("shared_brain")
    output = data.get("output")
    checks = {
        "status_completed": data.get("status") == "completed",
        "output_nonempty": isinstance(output, str) and bool(output.strip()),
        "marker_present": isinstance(output, str) and "NEXORA_AGENT_EXECUTION_OK" in output,
        "shared_brain_recalled": isinstance(brain, dict) and isinstance(brain.get("recall_count"), int),
        "shared_brain_writeback": isinstance(brain, dict) and brain.get("remembered") is True,
    }
    summary = {
        "task_id": data.get("task_id"),
        "role": data.get("role"),
        "status": data.get("status"),
        "shared_brain_recall_count": brain.get("recall_count") if isinstance(brain, dict) else None,
        "shared_brain_remembered": brain.get("remembered") if isinstance(brain, dict) else False,
        "checks": checks,
    }
    print("Live specialist smoke summary: " + json.dumps(summary, sort_keys=True))
    if not all(checks.values()):
        print("FAIL: live specialist execution did not satisfy all completion and memory checks.")
        return 1
    print("PASS: a real specialist model run completed and Shared Brain write-back succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
