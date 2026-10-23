import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company.nexora_growth_runtime import AGENTS, GrowthStore
from company.nexora_agent_executor import ProviderNotConfigured
from company import nexora_batch_executor as batch


class _InlineThread:
    def __init__(self, target, args=(), **kwargs):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


class GrowthBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = GrowthStore(Path(self.tmp.name) / "growth.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_batch_requires_configured_provider(self):
        with self.assertRaises(ProviderNotConfigured):
            batch.start_all_agents(self.store, {})

    def test_start_all_queues_and_processes_all_41_roles(self):
        def fake_execute(store, task_id):
            task = store.get_task(task_id)
            store.transition(task_id, "running", "test-agent")
            return store.transition(task_id, "completed", "test-agent",
                                    outputs={"draft": "internal test draft"},
                                    evidence_refs=[f"test:{task_id}"])

        with patch.object(batch, "execute_agent_draft", side_effect=fake_execute), \
             patch.object(batch.threading, "Thread", _InlineThread):
            result = batch.start_all_agents(self.store, {"GEMINI_API_KEY": "test-key"})

        self.assertTrue(result["started"])
        self.assertEqual(result["total"], 41)
        self.assertEqual(len(self.store.list_tasks(limit=100)), 41)
        self.assertEqual(batch.batch_status()["finished"], 41)
        self.assertEqual(batch.batch_status()["failed"], 0)
        self.assertFalse(batch.batch_status()["running"])

    def test_batch_continues_after_individual_task_failure(self):
        calls = []
        def fake_execute(store, task_id):
            calls.append(task_id)
            if len(calls) == 1:
                raise RuntimeError("simulated provider failure")
            task = store.get_task(task_id)
            store.transition(task_id, "running", "test-agent")
            return store.transition(task_id, "completed", "test-agent",
                                    outputs={"draft": "internal test draft"},
                                    evidence_refs=[f"test:{task_id}"])

        with patch.object(batch, "execute_agent_draft", side_effect=fake_execute), \
             patch.object(batch.threading, "Thread", _InlineThread):
            result = batch.start_all_agents(self.store, {"OPENAI_API_KEY": "test-key"})

        self.assertTrue(result["started"])
        self.assertEqual(len(calls), 41)
        self.assertEqual(batch.batch_status()["finished"], 41)
        self.assertEqual(batch.batch_status()["failed"], 1)
        self.assertFalse(batch.batch_status()["running"])


if __name__ == "__main__":
    unittest.main()
