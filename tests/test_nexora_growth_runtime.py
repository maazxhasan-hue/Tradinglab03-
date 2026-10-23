import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from company.nexora_growth_runtime import AGENT_DIRECTORY, AGENTS, COMPANY_AGENTS, DEPARTMENTS, GrowthStore
from company.nexora_agent_executor import execute_agent_draft, ProviderNotConfigured, DraftExecutionError, provider_status, role_deliverable_contract

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

    def test_requested_specialist_roles_are_registered_and_executable(self):
        required = {
            "Harvey Agent", "CEO / Strategy Lead", "Lead Discovery Agent",
            "Sales Agent", "Pricing Agent", "Client Support Agent", "Brand Agent",
            "Contact Agent", "Copywriter", "Social & Community Agent", "SEO Web Agent",
            "Growth Analysis Agent", "Product Manager Agent", "UX/UI Designer",
            "Frontend Developer", "Backend Developer", "Testing & QA Agent",
            "Security & Privacy Agent", "Release & Development Agent",
            "Documentation Specialist", "Project Operations Agent", "Finance Lead",
            "Policy & Compliance Agent", "Knowledge & Memory Agent", "Workflow Agent",
            "Customer Support Agent", "Experiment & Learning Agent", "Trading System Agent",
            "Reverse Writing Agent", "Cinematic Video Production Agent",
            "Instagram Growth Agent", "Video Editing Agent", "Website Making Agent",
            "Landing Page Agent", "Marketing Agent",
        }
        registered = {agent["name"] for agent in AGENT_DIRECTORY.values()}
        self.assertTrue(required.issubset(registered), sorted(required - registered))
        self.assertEqual(len(AGENT_DIRECTORY), len(AGENTS) + len(COMPANY_AGENTS))
        for agent in AGENT_DIRECTORY.values():
            task = self.store.create_task(
                "Capability smoke test: " + agent["name"], agent["agent_id"],
                {"goal": "Create a role-specific internal deliverable; draft-only."},
            )
            self.assertEqual(task["status"], "queued")
            self.assertEqual(task["agent_id"], agent["agent_id"])

    def test_role_contracts_produce_specialist_specific_acceptance_criteria(self):
        self.assertIn("timed shot-by-shot storyboard",
                      role_deliverable_contract("Cinematic Video Production Agent", "Creative & Presenting"))
        self.assertIn("file-by-file code or patch",
                      role_deliverable_contract("Website Making Agent", "Builders & Engineering"))
        self.assertIn("paper-trading-only",
                      role_deliverable_contract("Trading System Agent", "Quality, Audit & Testing"))
        self.assertIn("source-backed",
                      role_deliverable_contract("Lead Discovery Agent", "Sales & Partnerships"))
        self.assertIn("executive brief",
                      role_deliverable_contract("CEO / Strategy Lead", "Executive & Strategy"))
        self.assertIn("channel-specific growth asset",
                      role_deliverable_contract("Marketing Agent", "Marketing & Brand"))

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

    def test_provider_status_never_exposes_secret(self):
        self.assertEqual(provider_status({}), {"configured": False, "provider": None})
        self.assertEqual(provider_status({"GEMINI_API_KEY": "secret-value"}),
                         {"configured": True, "provider": "gemini"})
        self.assertEqual(provider_status({"OPENAI_API_KEY": "another-secret"}),
                         {"configured": True, "provider": "openai"})
        self.assertEqual(provider_status({"GEMINI_API_KEY": "  ", "OPENAI_API_KEY": ""}),
                         {"configured": False, "provider": None})

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

    def test_provider_status_reports_presence_without_exposing_secret(self):
        self.assertEqual(provider_status({}), {"configured": False, "provider": None})
        status = provider_status({"GEMINI_API_KEY":"secret-test-value"})
        self.assertEqual(status, {"configured": True, "provider": "gemini"})
        self.assertNotIn("secret-test-value", str(status))
        self.assertEqual(provider_status({"OPENAI_API_KEY":"secret-test-value"}),
                         {"configured": True, "provider": "openai"})

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
