import unittest
from unittest.mock import patch
import private_hq_server as hq


class GrowthBatchTests(unittest.TestCase):
    def setUp(self):
        with hq.BATCH_LOCK:
            hq.BATCH_STATE.update({"batch_id": "test", "running": True, "total": 2,
                                   "finished": 0, "failed": 0, "queued": 2,
                                   "started_at": "test", "finished_at": None})
            hq.BATCH_TASK_IDS[:] = ["task-a", "task-b"]

    def tearDown(self):
        with hq.BATCH_LOCK:
            hq.BATCH_STATE.update({"batch_id": None, "running": False, "total": 0,
                                   "finished": 0, "failed": 0, "queued": 0,
                                   "started_at": None, "finished_at": None})
            hq.BATCH_TASK_IDS.clear()

    def test_batch_runs_all_tasks_and_records_completion(self):
        with patch.object(hq, "execute_agent_draft") as execute:
            hq._run_growth_batch(["task-a", "task-b"])
        self.assertEqual(execute.call_count, 2)
        self.assertFalse(hq.BATCH_STATE["running"])
        self.assertEqual(hq.BATCH_STATE["finished"], 2)
        self.assertEqual(hq.BATCH_STATE["failed"], 0)
        self.assertEqual(hq.BATCH_STATE["queued"], 0)
        self.assertTrue(hq.BATCH_STATE["finished_at"])

    def test_batch_counts_failures_without_stopping_other_roles(self):
        def side_effect(store, task_id):
            if task_id == "task-a":
                raise RuntimeError("simulated provider failure")
            return {"status": "completed"}
        with patch.object(hq, "execute_agent_draft", side_effect=side_effect):
            hq._run_growth_batch(["task-a", "task-b"])
        self.assertEqual(hq.BATCH_STATE["finished"], 2)
        self.assertEqual(hq.BATCH_STATE["failed"], 1)
        self.assertFalse(hq.BATCH_STATE["running"])


if __name__ == "__main__":
    unittest.main()
