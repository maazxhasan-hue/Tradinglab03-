"""Live operational observability derived from persisted task records.

No simulated agent counts: task metrics come from GrowthStore rows. Cost remains
unknown unless a provider supplies usage/cost data; this module never guesses it.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def build_monitoring_snapshot(store, *, now: datetime | None = None, limit: int = 100) -> dict:
    """Build truthful health, task, retry, latency and actionable alert data."""
    current = now or datetime.now(timezone.utc)
    tasks = store.list_tasks(limit=max(1, min(int(limit), 250)))
    counts: dict[str, int] = {}
    alerts: list[dict[str, str]] = []
    rows: list[dict[str, Any]] = []
    durations: list[int] = []
    total_retries = 0
    provider_counts: dict[str, int] = {}

    for task in tasks:
        status = str(task.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        retries = int(task.get("retry_count") or 0)
        total_retries += retries
        outputs = task.get("outputs") if isinstance(task.get("outputs"), dict) else {}
        provider = outputs.get("provider")
        if provider:
            provider_counts[str(provider)] = provider_counts.get(str(provider), 0) + 1
        created, updated = _parse_time(task.get("created_at")), _parse_time(task.get("updated_at"))
        elapsed_ms = None
        if created and updated:
            elapsed_ms = max(0, int((updated - created).total_seconds() * 1000))
            if status == "completed":
                durations.append(elapsed_ms)
        error = task.get("error")
        item = {
            "task_id": task.get("task_id"),
            "title": task.get("title"),
            "agent_id": task.get("agent_id"),
            "department": task.get("department"),
            "status": status,
            "provider": provider,
            "elapsed_ms": elapsed_ms,
            "retry_count": retries,
            "error": error,
            "updated_at": task.get("updated_at"),
            "output_available": bool(outputs),
            "output_summary": str(outputs.get("draft") or outputs.get("summary") or "")[:240],
            "cost_usd": outputs.get("cost_usd") if isinstance(outputs.get("cost_usd"), (int, float)) else None,
        }
        rows.append(item)
        if status == "failed":
            alerts.append({"severity": "critical", "code": "task_failed",
                           "message": f"Task {task.get('task_id')} failed: {error or 'no error detail'}"})
        elif status == "blocked":
            alerts.append({"severity": "warning", "code": "task_blocked",
                           "message": f"Task {task.get('task_id')} is blocked"})
        elif status == "running" and updated and (current - updated).total_seconds() > 900:
            alerts.append({"severity": "warning", "code": "task_stale",
                           "message": f"Task {task.get('task_id')} has shown no update for over 15 minutes"})
        if retries >= 3:
            alerts.append({"severity": "warning", "code": "retry_exhaustion_risk",
                           "message": f"Task {task.get('task_id')} has {retries} recorded retries"})

    completed = counts.get("completed", 0)
    failed = counts.get("failed", 0)
    status = "degraded" if failed or any(a["severity"] == "critical" for a in alerts) else "ok"
    return {
        "source": "persisted_task_records",
        "generated_at": current.isoformat(),
        "health": status,
        "task_counts": counts,
        "tasks_observed": len(rows),
        "completed": completed,
        "failed": failed,
        "success_rate": round(completed / (completed + failed), 4) if completed + failed else None,
        "total_recorded_retries": total_retries,
        "completed_lifecycle_elapsed_ms_avg": round(sum(durations) / len(durations)) if durations else None,
        "provider_counts": provider_counts,
        "cost_usd_total": round(sum(float(t["cost_usd"]) for t in rows if t["cost_usd"] is not None), 8)
                          if any(t["cost_usd"] is not None for t in rows) else None,
        "cost_note": "null means provider cost/usage was not reported; no cost is estimated.",
        "alerts": alerts[:100],
        "tasks": rows,
    }
