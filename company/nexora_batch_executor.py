"""Bounded background runner for all 196 Nexora internal-draft roles.

Runs one provider request at a time. This module never publishes or contacts anyone.
"""
from __future__ import annotations

import threading
from typing import Mapping

from company.nexora_growth_runtime import AGENT_DIRECTORY, AGENTS, COMPANY_AGENTS, GrowthStore
from company.nexora_agent_executor import (
    ProviderNotConfigured, execute_agent_draft, provider_status,
)

_lock = threading.Lock()
_state_lock = threading.Lock()
_state: dict = {"running": False, "batch_id": None, "scope": None, "total": 0, "finished": 0,
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




def resume_queued_tasks(store: GrowthStore, environ: Mapping[str, str] | None = None) -> dict:
    """Resume persisted queued tasks after a process restart, when an AI provider is configured."""
    if not provider_status(environ)["configured"]:
        return {"started": False, "reason": "provider_not_configured", "queued": 0}
    if not _lock.acquire(blocking=False):
        return {"started": False, "reason": "batch_already_running", **batch_status()}
    try:
        queued = store.list_tasks(status="queued", limit=250)
        task_ids = [task["task_id"] for task in queued]
        if not task_ids:
            _lock.release()
            return {"started": False, "reason": "no_queued_tasks", "queued": 0}
        import uuid
        with _state_lock:
            _state.update({"running": True, "batch_id": str(uuid.uuid4()), "scope": "recovered_queue",
                           "total": len(task_ids), "finished": 0, "failed": 0, "last_error": None})
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
                    "role": agent["name"],
                    "department": agent["department"],
                    "mission": mission,
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
                           "total": len(task_ids), "finished": 0, "failed": 0, "last_error": None})
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
    """Queue all 196 registered roles and begin sequential internal draft generation."""
    if not provider_status(environ)["configured"]:
        raise ProviderNotConfigured(
            "Configure OPENROUTER_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in the private HQ runtime before starting all agents."
        )
    if not _lock.acquire(blocking=False):
        return {"started": False, "reason": "batch_already_running", **batch_status()}

    try:
        tasks = []
        for agent in AGENT_DIRECTORY.values():
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
            _state.update({"running": True, "batch_id": str(uuid.uuid4()), "scope": "all_196", "total": len(tasks),
                           "finished": 0, "failed": 0, "last_error": None})
        thread = threading.Thread(target=_worker, args=(store, tasks), daemon=True,
                                  name="nexora-196-agent-draft-batch")
        thread.start()
        return {"started": True, "task_ids": tasks, **batch_status()}
    except Exception:
        _lock.release()
        raise
