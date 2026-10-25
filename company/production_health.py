"""Live, privacy-safe readiness probes for Nexora's shared brain.

This performs a read-only recall against the configured service. It intentionally
does not write probe memories or return memory content in the health response.
"""
from __future__ import annotations

from typing import Any


def check_shared_brain() -> dict[str, Any]:
    """Verify an actual authenticated shared-brain recall, not just env-key presence."""
    from company.shared_brain import SharedBrainClient, SharedBrainError

    client = SharedBrainClient()
    if not client.configured:
        return {
            "status": "not_configured",
            "operation": "recall",
            "memory_count": None,
            "error": "machine_credentials_not_configured",
        }
    try:
        memories = client.recall(
            project_key="nexora",
            namespace="company",
            query="Nexora production readiness check",
            limit=1,
        )
    except SharedBrainError as exc:
        # SharedBrainError messages are sanitized by the client; never return payloads.
        message = str(exc)
        if "HTTP 401" in message or "HTTP 403" in message:
            error = "authentication_rejected"
        elif "HTTP 429" in message:
            error = "rate_limited"
        else:
            error = "request_failed"
        return {
            "status": "degraded",
            "operation": "recall",
            "memory_count": None,
            "error": error,
        }
    except Exception:
        return {
            "status": "degraded",
            "operation": "recall",
            "memory_count": None,
            "error": "unexpected_probe_failure",
        }
    return {
        "status": "ok",
        "operation": "recall",
        "memory_count": len(memories),
        "error": None,
    }
