import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from company.nexora_growth_runtime import AGENTS, DEPARTMENTS, GrowthStore
from company.nexora_agent_executor import execute_agent_draft, ProviderNotConfigured, DraftExecutionError

class GrowthRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = GrowthStore(Path(self.tmp.name) / "growth.sqlite3")
    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_41_agent_shape(self):
        self.assertEqual(len(AGENTS), 41)
        self.assertEqual(sum(a["kind"] == "director" for a in AGENTS), 1)
        self.assertEqual(sum(a["kind"] == "lead" for a in AGENTS), 8)
        self.assertEqual(sum(a["kind"] == "specialist" for a in AGENTS), 32)
        self.assertEqual(len(DEPARTMENTS), 8)

    def test_task_persistence_and_evidence_required(self):
        task = self.store.create_task("Draft Nexora launch reel", "d01-a02", {"service":"AI automation"})
        self.assertEqual(self.store.get_task(task["task_id"])["status"], "queued")
        self.store.transition(task["task_id"], "running", "test")
        with self.assertRaises(ValueError):
            self.store.transition(task["task_id"], "completed", "test", outputs={"caption":"draft"})
        result = self.store.transition(task["task_id"], "completed", "test",
                                       outputs={"caption":"draft"}, evidence_refs=["test:caption"])
        self.assertEqual(result["status"], "completed")

    def test_sensitive_action_fails_closed_and_requires_separate_approver(self):
        req = self.store.request_approval("publish_content", "campaign-123", "content-agent")
        self.assertFalse(self.store.authorize_external_action(req["approval_id"], "publish_content", "campaign-123")[0])
        with self.assertRaises(ValueError):
            self.store.decide_approval(req["approval_id"], "content-agent", True, "self approval")
        decision = self.store.decide_approval(req["approval_id"], "owner", True, "Owner approved this exact campaign")
        self.assertTrue(self.store.authorize_external_action(decision["approval_id"], "publish_content", "campaign-123")[0])
        self.assertFalse(self.store.authorize_external_action(decision["approval_id"], "publish_content", "other-campaign")[0])

    def test_approval_cannot_be_changed_twice(self):
        req = self.store.request_approval("send_public_reply", "comment-1", "agent")
        self.store.decide_approval(req["approval_id"], "owner", False, "Needs edits")
        with self.assertRaises(ValueError):
            self.store.decide_approval(req["approval_id"], "owner", True, "Changed mind")

    def test_bad_transitions_and_unknown_agents_rejected(self):
        with self.assertRaises(ValueError):
            self.store.create_task("bad", "not-an-agent")
        task = self.store.create_task("Task", "growth-director")
        with self.assertRaises(ValueError):
            self.store.transition(task["task_id"], "completed", "test", outputs={}, evidence_refs=["x"])

    def test_ai_agent_generates_private_draft_and_records_evidence(self):
        task = self.store.create_task("Draft a launch reel", "d01-a02",
                                      {"context":"Audience: small businesses"})
        with patch("company.nexora_agent_executor._call_provider", return_value="Draft caption for review"):
            result = execute_agent_draft(self.store, task["task_id"],
                                         {"GEMINI_API_KEY":"test-key"})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["outputs"]["draft"], "Draft caption for review")
        self.assertEqual(result["outputs"]["mode"], "draft_only")
        self.assertIn(f"task:{task['task_id']}:internal-draft", result["evidence_refs"])

    def test_ai_agent_fails_closed_without_provider_key(self):
        task = self.store.create_task("Draft a launch reel", "d01-a02")
        with self.assertRaises(ProviderNotConfigured):
            execute_agent_draft(self.store, task["task_id"], {})
        self.assertEqual(self.store.get_task(task["task_id"])["status"], "queued")

    def test_ai_agent_records_provider_failure_without_fake_completion(self):
        task = self.store.create_task("Draft a launch reel", "d01-a02")
        with patch("company.nexora_agent_executor._call_provider",
                   side_effect=DraftExecutionError("provider unavailable")):
            with self.assertRaises(DraftExecutionError):
                execute_agent_draft(self.store, task["task_id"], {"OPENAI_API_KEY":"test-key"})
        self.assertEqual(self.store.get_task(task["task_id"])["status"], "failed")
        self.assertNotIn("draft", self.store.get_task(task["task_id"])["outputs"])

if __name__ == "__main__":
    unittest.main()
