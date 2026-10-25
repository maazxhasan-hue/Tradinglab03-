"""Bounded background runner for all 196 Nexora internal-draft roles.

Runs a small bounded pool of provider requests. Never publishes or contacts anyone.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Mapping

from company.nexora_growth_runtime import AGENT_DIRECTORY, AGENTS, COMPANY_AGENTS, GrowthStore
from company.nexora_agent_executor import (
    DraftExecutionError, ProviderNotConfigured, execute_agent_draft, provider_status,
)

_lock = threading.Lock()
_state_lock = threading.Lock()
_state: dict = {"running": False, "batch_id": None, "scope": None, "total": 0, "finished": 0,
                "failed": 0, "last_error": None, "retry_count": 0}


def batch_status() -> dict:
    with _state_lock:
        return dict(_state)


# Free/shared providers often enforce a quota across the entire API key.
# Serialize requests and share a cooldown after HTTP 429 to prevent retry storms.
MAX_PARALLEL_TASKS = 1
MAX_TASK_ATTEMPTS = 5
# Shared/free-tier providers may need a longer reset window. Back off globally
# on 429s so every queued agent does not immediately repeat the same failure.
RATE_LIMIT_COOLDOWN_SECONDS = 60
MAX_RATE_LIMIT_COOLDOWN_SECONDS = 300
_provider_gate = threading.Lock()
_provider_cooldown_until = 0.0

def _wait_for_provider_slot() -> None:
    while True:
        with _provider_gate:
            remaining = _provider_cooldown_until - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 2.0))

def _cool_down_provider(seconds: float = RATE_LIMIT_COOLDOWN_SECONDS) -> None:
    global _provider_cooldown_until
    with _provider_gate:
        _provider_cooldown_until = max(
            _provider_cooldown_until,
            time.monotonic() + min(MAX_RATE_LIMIT_COOLDOWN_SECONDS, max(1.0, seconds)),
        )
# execute_agent_draft deliberately converts provider responses into safe categories.
# Retry those categories here; raw provider bodies/credentials must never be logged.
RETRYABLE_MARKERS = (
    "HTTP 408", "HTTP 425", "HTTP 429", "HTTP 500", "HTTP 502",
    "HTTP 503", "HTTP 504", "request failed", "availability and TLS",
    "ProviderRateLimitError", "ProviderTemporaryServerError",
    "ProviderNetworkOrTLSError",
)


def _run_one(store: GrowthStore, task_id: str) -> str | None:
    """Retry transient provider failures only; never log provider bodies or secrets."""
    for attempt in range(1, MAX_TASK_ATTEMPTS + 1):
        try:
            _wait_for_provider_slot()
            execute_agent_draft(store, task_id)
            if attempt > 1:
                with _state_lock:
                    _state["retry_count"] += attempt - 1
            return None
        except ProviderNotConfigured:
            return "ProviderNotConfigured"
        except Exception as exc:
            message = str(exc)
            rate_limited = (
                isinstance(exc, DraftExecutionError)
                and ("HTTP 429" in message or "ProviderRateLimitError" in message)
            )
            if rate_limited:
                # Exponential cooldown across attempts, capped to avoid an endless sleep.
                _cool_down_provider(min(
                    RATE_LIMIT_COOLDOWN_SECONDS * (2 ** (attempt - 1)),
                    MAX_RATE_LIMIT_COOLDOWN_SECONDS,
                ))
            retryable = isinstance(exc, DraftExecutionError) and any(
                marker in message for marker in RETRYABLE_MARKERS
            )
            if not retryable or attempt >= MAX_TASK_ATTEMPTS:
                if attempt > 1:
                    with _state_lock:
                        _state["retry_count"] += attempt - 1
                # Return only a bounded, non-secret classification. Never return provider response bodies.
                if "HTTP 401" in message or "HTTP 403" in message or "ProviderAuthenticationOrPermissionError" in message:
                    return "ProviderAuthenticationOrPermissionError"
                if "HTTP 429" in message or "ProviderRateLimitError" in message:
                    return "ProviderRateLimitError"
                if any(f"HTTP {code}" in message for code in (500, 502, 503, 504)) or "ProviderTemporaryServerError" in message:
                    return "ProviderTemporaryServerError"
                if "request failed" in message or "availability and TLS" in message or "ProviderNetworkOrTLSError" in message:
                    return "ProviderNetworkOrTLSError"
                # DraftExecutionError messages are already sanitized by the executor.
                # Preserve that safe category instead of collapsing every failure to
                # the unhelpful generic label "DraftExecutionError".
                if isinstance(exc, DraftExecutionError) and message:
                    return message[:100]
                return type(exc).__name__
            # Exponential backoff with a small cap to reduce rate-limit pressure.
            # Do not hammer shared providers. Rate limits use the shared cooldown;
            # other transient failures use short exponential backoff.
            if not rate_limited:
                time.sleep(min(2 ** (attempt - 1), 8))
    return "UnknownExecutionError"


def _worker(store: GrowthStore, task_ids: list[str]) -> None:
    failures = 0
    last_error = None
    try:
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_TASKS, thread_name_prefix="nexora-agent") as pool:
            futures = [pool.submit(_run_one, store, task_id) for task_id in task_ids]
            for future in as_completed(futures):
                error_type = future.result()
                with _state_lock:
                    _state["finished"] += 1
                    if error_type:
                        failures += 1
                        last_error = error_type
                    _state["failed"] = failures
                    _state["last_error"] = last_error
    finally:
        with _state_lock:
            _state["running"] = False
        _lock.release()


def resume_queued_tasks(store: GrowthStore, environ: Mapping[str, str] | None = None) -> dict:
    """Resume persisted queued tasks after a process restart, when an AI provider is configured."""
    if not provider_status(environ)["configured"]:
        return {"started": False, "reason": "provider_not_configured", "queued": 0}
    if not _lock.acquire(blocking=False):
        return {"started": False, "reason": "batch_already_running", **batch_status()}
    try:
        recovered_running = store.requeue_interrupted_tasks(limit=250)
        queued = store.list_tasks(status="queued", limit=250)
        task_ids = [task["task_id"] for task in queued]
        if not task_ids:
            _lock.release()
            return {"started": False, "reason": "no_queued_tasks", "queued": 0}
        import uuid
        with _state_lock:
            _state.update({"running": True, "batch_id": str(uuid.uuid4()), "scope": "recovered_queue",
                           "total": len(task_ids), "finished": 0, "failed": 0, "last_error": None,
                           "retry_count": 0, "recovered_interrupted": recovered_running})
        thread = threading.Thread(target=_worker, args=(store, task_ids), daemon=True,
                                  name="nexora-queued-task-recovery")
        thread.start()
        return {"started": True, "scope": "recovered_queue", "queued": len(task_ids), **batch_status()}
    except Exception:
        _lock.release()
        raise


def start_company_workforce(store: GrowthStore, mission: str,
                            environ: Mapping[str, str] | None = None) -> dict:
    """Run the complete company role registry and the 41 growth roles as real AI draft tasks."""
    if not provider_status(environ)["configured"]:
        raise ProviderNotConfigured(
            "Configure OPENROUTER_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in the private HQ runtime."
        )
    mission = mission.strip()
    if not mission or len(mission) > 4000:
        raise ValueError("Mission must be 1-4000 characters.")
    if not _lock.acquire(blocking=False):
        return {"started": False, "reason": "batch_already_running", **batch_status()}
    try:
        task_ids = []
        for agent in AGENT_DIRECTORY.values():
            task = store.create_task(
                title=f"{agent['name']}: company mission - {mission[:100]}",
                agent_id=agent["agent_id"],
                inputs={
                    "role": agent["name"], "department": agent["department"], "mission": mission,
                    "goal": "Produce the assigned role-specific deliverable for this company mission.",
                    "instructions": (
                        f"Own the work of {agent['name']} in {agent['department']}. "
                        "Produce concrete internal work, state evidence and assumptions, and identify handoffs. "
                        "Do not publish, send messages, spend money, or claim actions that were not performed."
                    ),
                    "mode": "draft_only",
                },
            )
            task_ids.append(task["task_id"])
        import uuid
        with _state_lock:
            _state.update({"running": True, "batch_id": str(uuid.uuid4()), "scope": "full_company",
                           "total": len(task_ids), "finished": 0, "failed": 0, "last_error": None,
                           "retry_count": 0})
        thread = threading.Thread(target=_worker, args=(store, task_ids), daemon=True,
                                  name="nexora-full-company-workforce")
        thread.start()
        return {"started": True, "scope": "full_company", "task_ids": task_ids,
                "company_roles": len(COMPANY_AGENTS), "growth_roles": len(AGENTS),
                "total": len(task_ids), **batch_status()}
    except Exception:
        _lock.release()
        raise


def start_all_agents(store: GrowthStore, environ: Mapping[str, str] | None = None) -> dict:
    """Queue the canonical 41 growth roles for bounded-parallel internal draft generation."""
    if not provider_status(environ)["configured"]:
        raise ProviderNotConfigured(
            "Configure OPENROUTER_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in the private HQ runtime before starting all agents."
        )
    if not _lock.acquire(blocking=False):
        return {"started": False, "reason": "batch_already_running", **batch_status()}

    try:
        tasks = []
        for agent in AGENTS:
            task = store.create_task(
                title=f"Growth sprint: {agent['name']} deliverable for @nexoraai03",
                agent_id=agent["agent_id"],
                inputs={
                    "campaign": "Nexora AI social growth sprint",
                    "instagram_account": "nexoraai03",
                    "goal": "Prepare a practical, evidence-aware deliverable to improve reach, engagement, qualified enquiries, and conversion.",
                    "instructions": (
                        f"Act only within your role: {agent['name']} ({agent['department']}). "
                        "Produce a concrete deliverable, state assumptions and missing evidence, "
                        "and hand off useful next steps to the next role. Draft only; do not publish, "
                        "send messages, contact leads, spend money, or claim external actions."
                    ),
                },
            )
            tasks.append(task["task_id"])
        import uuid
        with _state_lock:
            _state.update({"running": True, "batch_id": str(uuid.uuid4()), "scope": "growth_41",
                           "total": len(tasks), "finished": 0, "failed": 0, "last_error": None,
                           "retry_count": 0})
        thread = threading.Thread(target=_worker, args=(store, tasks), daemon=True,
                                  name="nexora-growth-agent-draft-batch")
        thread.start()
        return {"started": True, "task_ids": tasks, **batch_status()}
    except Exception:
        _lock.release()
        raise
