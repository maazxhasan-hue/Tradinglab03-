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
        with patch.dict("os.environ",{"AI_PROVIDER":"openai"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"OPENAI_API_KEY"):
                call_model("draft_proposal","title","context",api_key="",provider="openai")

    def test_gemini_native_provider_uses_key_header_and_parses_text(self):
        import io, json
        from unittest.mock import patch
        from company.agent_runtime import call_model
        response = io.BytesIO(json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Gemini draft output"}]}}]
        }).encode())
        response.__enter__ = lambda self: self
        response.__exit__ = lambda *args: None
        with patch("company.agent_runtime.urllib.request.urlopen", return_value=response) as urlopen:
            result = call_model("draft_proposal", "Test title", "Test brief",
                                api_key="test-secret", provider="gemini", model="gemini-test")
        self.assertEqual(result, "Gemini draft output")
        request = urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/models/gemini-test:generateContent"))
        self.assertEqual(request.get_header("X-goog-api-key"), "test-secret")
        payload = json.loads(request.data.decode())
        self.assertIn("systemInstruction", payload)
        self.assertEqual(payload["contents"][0]["role"], "user")

    def test_gemini_provider_requires_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
                call_model("draft_proposal", "title", "context", provider="gemini", api_key="")

    def test_free_template_mode_needs_no_key(self):
        with patch.dict("os.environ",{},clear=True):
            output = call_model("draft_proposal","Landing page","Need a simple landing page")
        self.assertIn("free template mode", output)
        self.assertIn("Landing page", output)

    def test_free_templates_cover_all_allowed_tasks(self):
        for task_type in ALLOWED_TASKS:
            output = call_model(task_type,"Example","Example brief")
            self.assertTrue(output.strip())
    def test_only_allowlisted_tasks(self):
        self.assertEqual(ALLOWED_TASKS,{"draft_proposal","draft_website_copy","summarize_opportunity"})

if __name__ == "__main__": unittest.main()
