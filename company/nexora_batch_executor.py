"""Bounded background runner for all 41 Nexora internal-draft roles.

Runs one provider request at a time. This module never publishes or contacts anyone.
"""
from __future__ import annotations

import threading
from typing import Mapping

from company.nexora_growth_runtime import AGENTS, GrowthStore
from company.nexora_agent_executor import (
    DraftExecutionError, ProviderNotConfigured, execute_agent_draft, provider_status,
)

_lock = threading.Lock()
_state_lock = threading.Lock()
_state: dict = {"running": False, "batch_id": None, "total": 0, "finished": 0,
                "failed": 0, "last_error": None}


def batch_status() -> dict:
    with _state_lock:
        return dict(_state)


def _worker(store: GrowthStore, task_ids: list[str]) -> None:
    failures = 0
    last_error = None
    try:
        for task_id in task_ids:
            try:
                execute_agent_draft(store, task_id)
            except Exception as exc:
                failures += 1
                # One unexpected task failure must not terminate the remaining roles.
                # Record only the exception class, never provider responses or secrets.
                last_error = type(exc).__name__
            finally:
                with _state_lock:
                    _state["finished"] += 1
                    _state["failed"] = failures
                    _state["last_error"] = last_error
    finally:
        with _state_lock:
            _state["running"] = False
        _lock.release()


def start_all_agents(store: GrowthStore, environ: Mapping[str, str] | None = None) -> dict:
    """Queue all 41 roles and begin sequential internal draft generation."""
    if not provider_status(environ)["configured"]:
        raise ProviderNotConfigured(
            "Configure GEMINI_API_KEY or OPENAI_API_KEY in Render before starting all agents."
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
            _state.update({"running": True, "batch_id": str(uuid.uuid4()), "total": len(tasks),
                           "finished": 0, "failed": 0, "last_error": None})
        thread = threading.Thread(target=_worker, args=(store, tasks), daemon=True,
                                  name="nexora-41-agent-draft-batch")
        thread.start()
        return {"started": True, "task_ids": tasks, **batch_status()}
    except Exception:
        _lock.release()
        raise
