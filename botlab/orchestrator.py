"""Local job state coordinator. No network access, publishing, or external side effects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import hashlib, json
from pathlib import Path

@dataclass
class Job:
    job_id: str
    kind: str
    payload: dict[str, Any]
    state: str = "queued"
    notes: list[str] = field(default_factory=list)

class LocalOrchestrator:
    def __init__(self, state_path: str = "data/orchestrator_state.json"):
        self.state_path = Path(state_path)
        self.jobs: dict[str, Job] = {}
        if self.state_path.exists():
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.jobs = {k: Job(**v) for k, v in raw.items()}

    def enqueue(self, kind: str, payload: dict[str, Any]) -> Job:
        canonical = json.dumps({"kind": kind, "payload": payload}, sort_keys=True, ensure_ascii=False)
        job_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        if job_id not in self.jobs:
            self.jobs[job_id] = Job(job_id, kind, payload)
            self._save()
        return self.jobs[job_id]

    def transition(self, job_id: str, state: str, note: str = "") -> Job:
        allowed = {
            "queued": {"in_progress", "blocked", "cancelled"},
            "in_progress": {"pending_approval", "blocked", "failed", "cancelled"},
            "pending_approval": {"approved", "rejected", "cancelled"},
            "approved": {"scheduled"}, "scheduled": {"published", "failed", "cancelled"},
            "failed": {"queued", "cancelled"}, "blocked": {"queued", "cancelled"},
            "rejected": set(), "published": set(), "cancelled": set(),
        }
        job = self.jobs[job_id]
        if state not in allowed.get(job.state, set()):
            raise ValueError(f"Invalid job transition: {job.state} -> {state}")
        job.state = state
        if note: job.notes.append(note)
        self._save()
        return job

    def _save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps({k: vars(v) for k, v in self.jobs.items()},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
