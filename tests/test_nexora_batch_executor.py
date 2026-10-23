import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from company.nexora_growth_runtime import AGENT_DIRECTORY, AGENTS, COMPANY_AGENTS, GrowthStore
from company.nexora_agent_executor import ProviderNotConfigured, execute_agent_draft
from company.nexora_batch_executor import batch_status, start_all_agents, start_company_workforce


class BatchExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = GrowthStore(Path(self.tmp.name) / "growth.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_batch_requires_provider_key_before_queueing(self):
        with self.assertRaises(ProviderNotConfigured):
            start_all_agents(self.store, {})
        self.assertEqual(self.store.list_tasks(), [])

    def test_batch_queues_all_41_and_runs_draft_only_tasks(self):
        with patch("company.nexora_batch_executor.execute_agent_draft",
                   side_effect=lambda store, task_id: store.transition(
                       task_id, "running", "test-worker") and store.transition(
                       task_id, "completed", "test-worker",
                       outputs={"draft": "test draft", "mode": "draft_only"},
                       evidence_refs=["test:internal-draft"])):
            result = start_all_agents(self.store, {"GEMINI_API_KEY": "test-key"})
            self.assertTrue(result["started"])
            self.assertEqual(result["total"], 41)
            deadline = time.time() + 5
            while batch_status()["running"] and time.time() < deadline:
                time.sleep(0.01)
        state = batch_status()
        self.assertFalse(state["running"])
        self.assertEqual(state["finished"], 41)
        self.assertEqual(state["failed"], 0)
        tasks = self.store.list_tasks()
        self.assertEqual(len(tasks), len(AGENTS))
        self.assertTrue(all(task["status"] == "completed" for task in tasks))
        self.assertTrue(all(task["outputs"]["mode"] == "draft_only" for task in tasks))


    def test_unexpected_agent_error_does_not_stop_remaining_roles(self):
        calls = {"count": 0}

        def execute(store, task_id):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("simulated unexpected worker error")
            store.transition(task_id, "running", "test-worker")
            store.transition(
                task_id, "completed", "test-worker",
                outputs={"draft": "test draft", "mode": "draft_only"},
                evidence_refs=["test:internal-draft"],
            )

        with patch("company.nexora_batch_executor.execute_agent_draft", side_effect=execute):
            result = start_all_agents(self.store, {"OPENAI_API_KEY": "test-key"})
            self.assertTrue(result["started"])
            deadline = time.time() + 5
            while batch_status()["running"] and time.time() < deadline:
                time.sleep(0.01)

        state = batch_status()
        self.assertFalse(state["running"])
        self.assertEqual(state["finished"], 41)
        self.assertEqual(state["failed"], 1)
        self.assertEqual(calls["count"], 41)
        completed = [task for task in self.store.list_tasks() if task["status"] == "completed"]
        self.assertEqual(len(completed), 40)


    def test_full_company_workforce_queues_every_registered_role(self):
        def execute(store, task_id):
            store.transition(task_id, "running", "test-worker")
            store.transition(task_id, "completed", "test-worker",
                             outputs={"draft": "test draft", "mode": "draft_only"},
                             evidence_refs=["test:internal-draft"])
        with patch("company.nexora_batch_executor.execute_agent_draft", side_effect=execute):
            result = start_company_workforce(
                self.store, "Complete pending company work safely.",
                {"OPENROUTER_API_KEY": "test-key"},
            )
            self.assertTrue(result["started"])
            self.assertEqual(result["scope"], "full_company")
            self.assertEqual(result["total"], len(AGENT_DIRECTORY))
            deadline = time.time() + 10
            while batch_status()["running"] and time.time() < deadline:
                time.sleep(0.01)
        state = batch_status()
        self.assertFalse(state["running"])
        self.assertEqual(state["finished"], len(AGENT_DIRECTORY))
        self.assertEqual(state["failed"], 0)
        self.assertEqual(len(self.store.list_tasks(limit=250)), len(AGENT_DIRECTORY))

    def test_company_role_can_recall_and_write_shared_local_brain(self):
        agent = COMPANY_AGENTS[0]
        task = self.store.create_task(
            "Test company role memory", agent["agent_id"],
            {"role": agent["name"], "department": agent["department"], "mission": "Test shared memory"},
        )
        with patch("company.nexora_agent_executor._call_provider", return_value="Verified role deliverable"):
            result = execute_agent_draft(self.store, task["task_id"], {"OPENAI_API_KEY": "test-key"})
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["outputs"]["brain"]["local_memory_saved"])
        memories = self.store.recall_memories(agent["name"] + " Test company role memory", limit=5)
        self.assertTrue(any(m["source_agent"] == agent["agent_id"] for m in memories))


if __name__ == "__main__":
    unittest.main()
