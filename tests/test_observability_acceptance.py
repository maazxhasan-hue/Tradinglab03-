from company.nexora_growth_runtime import AGENT_DIRECTORY, GrowthStore


def test_task_lifecycle_and_restart_recovery_persist(tmp_path):
    db = tmp_path / "nexora.sqlite3"
    store = GrowthStore(db)
    agent_id = next(iter(AGENT_DIRECTORY))
    task = store.create_task("Acceptance test lifecycle", agent_id, {"context": "test"})
    assert task["status"] == "queued"
    store.transition(task["task_id"], "running", "acceptance-test")

    # Simulate process restart by creating a new store over the same persisted DB.
    restarted = GrowthStore(db)
    assert restarted.requeue_interrupted_tasks() == 1
    recovered = restarted.get_task(task["task_id"])
    assert recovered["status"] == "queued"
    assert "restart" in (recovered["error"] or "").lower()

    restarted.transition(task["task_id"], "running", "acceptance-test")
    completed = restarted.transition(
        task["task_id"], "completed", "acceptance-test",
        outputs={"draft": "verified test output", "provider": "test-fixture"},
        evidence_refs=["acceptance-test:verified"],
    )
    assert completed["status"] == "completed"
    assert completed["outputs"]["draft"] == "verified test output"
    assert completed["evidence_refs"] == ["acceptance-test:verified"]


def test_local_brain_memory_survives_store_reinitialization(tmp_path):
    db = tmp_path / "nexora.sqlite3"
    store = GrowthStore(db)
    store.remember_memory(
        "acceptance:memory-persistence",
        "Monitoring restart acceptance memory",
        {"check": "persisted"},
        source_agent="acceptance-test",
    )
    restarted = GrowthStore(db)
    recalled = restarted.recall_memories("monitoring restart acceptance", limit=5)
    assert any(item["memory_key"] == "acceptance:memory-persistence" for item in recalled)
