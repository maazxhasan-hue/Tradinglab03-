import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from company.agent_runtime import TaskQueue, call_model, ALLOWED_TASKS

class AgentRuntimeTests(unittest.TestCase):
    def test_queue_enqueue_claim_and_complete(self):
        with tempfile.TemporaryDirectory() as td:
            q=TaskQueue(Path(td)/"tasks.sqlite3")
            task_id=q.enqueue("draft_proposal","Landing page proposal","Client needs a landing page")
            task=q.claim_next()
            self.assertEqual(task["id"],task_id)
            self.assertEqual(task["status"],"queued")
            self.assertIsNone(q.claim_next())
            q.finish(task_id,"data/agent_outputs/task-1.md")
            self.assertEqual(q.list_tasks()[0]["status"],"completed")
    def test_reject_unsupported_task(self):
        with tempfile.TemporaryDirectory() as td:
            q=TaskQueue(Path(td)/"tasks.sqlite3")
            with self.assertRaises(ValueError):
                q.enqueue("run_shell","danger","execute code")
    def test_context_limit(self):
        with tempfile.TemporaryDirectory() as td:
            q=TaskQueue(Path(td)/"tasks.sqlite3")
            with self.assertRaises(ValueError):
                q.enqueue("draft_website_copy","x","a"*12001)
    def test_model_requires_key(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaisesRegex(RuntimeError,"OPENAI_API_KEY"):
                call_model("draft_proposal","title","context",api_key="")
    def test_only_allowlisted_tasks(self):
        self.assertEqual(ALLOWED_TASKS,{"draft_proposal","draft_website_copy","summarize_opportunity"})

if __name__ == "__main__": unittest.main()
