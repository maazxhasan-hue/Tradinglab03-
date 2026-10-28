from datetime import datetime, timezone
from company.observability import build_monitoring_snapshot


class FakeStore:
    def list_tasks(self, limit=100):
        return [
            {"task_id":"done-1","title":"Research","agent_id":"research","department":"Research",
             "status":"completed","retry_count":1,"error":None,
             "created_at":"2026-01-01T00:00:00+00:00","updated_at":"2026-01-01T00:00:02+00:00",
             "outputs":{"provider":"openrouter","draft":"Evidence-backed output"}},
            {"task_id":"bad-1","title":"Draft","agent_id":"writer","department":"Content",
             "status":"failed","retry_count":3,"error":"ProviderRateLimitError",
             "created_at":"2026-01-01T00:00:00+00:00","updated_at":"2026-01-01T00:00:03+00:00",
             "outputs":{}},
        ][:limit]


def test_snapshot_uses_persisted_tasks_and_reports_failures():
    snapshot = build_monitoring_snapshot(FakeStore(), now=datetime(2026,1,1,tzinfo=timezone.utc))
    assert snapshot["source"] == "persisted_task_records"
    assert snapshot["tasks_observed"] == 2
    assert snapshot["task_counts"] == {"completed": 1, "failed": 1}
    assert snapshot["health"] == "degraded"
    assert snapshot["total_recorded_retries"] == 4
    assert snapshot["completed_lifecycle_elapsed_ms_avg"] == 2000
    assert snapshot["provider_counts"] == {"openrouter": 1}
    assert snapshot["cost_usd_total"] is None
    assert any(a["code"] == "task_failed" for a in snapshot["alerts"])
    assert any(a["code"] == "retry_exhaustion_risk" for a in snapshot["alerts"])


def test_cost_is_not_invented_when_provider_does_not_report_it():
    snapshot = build_monitoring_snapshot(FakeStore())
    assert snapshot["cost_usd_total"] is None
    assert "no cost is estimated" in snapshot["cost_note"]
