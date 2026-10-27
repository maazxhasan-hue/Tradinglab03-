"""Regression tests for canonical role-specific prompts across the whole roster."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "harvey-worker"
sys.path.insert(0, str(ROOT))

# Isolate this import's database side effects from the developer's real data.
_TEST_DB = tempfile.TemporaryDirectory(prefix="nexora-agent-mandates-")
os.environ.pop("DATABASE_URL", None)
os.environ["DATABASE_PATH"] = str(Path(_TEST_DB.name) / "test.db")

_SPEC = importlib.util.spec_from_file_location("nexora_agent_mandate_test_app", WORKER / "app.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Could not load Harvey worker module for prompt tests")
_APP = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP)


class AgentPromptMandateTests(unittest.TestCase):
    def test_every_registered_role_receives_its_canonical_mandate(self):
        self.assertGreaterEqual(len(_APP.AGENT_MANDATES), 150)
        for role, mandate in _APP.AGENT_MANDATES.items():
            with self.subTest(role=role):
                prompt = _APP._agent_system_prompt(role)
                self.assertIn("Role: " + role, prompt)
                self.assertIn("Canonical role mandate: " + mandate, prompt)

    def test_knowledge_and_memory_role_is_not_generic(self):
        role = "Knowledge & Memory"
        prompt = _APP._agent_system_prompt(role)
        self.assertIn("Maintain decision logs, reusable knowledge, provenance, and change history.", prompt)


    def test_registry_mandates_are_responsibility_specific(self):
        sales = _APP._registry_role_mandate("Lead Researcher", "Sales & Partnerships")
        security = _APP._registry_role_mandate("Security Reviewer", "Quality, Audit & Testing")
        creative = _APP._registry_role_mandate("Video Editor", "Creative & Presenting")
        self.assertIn("lawful public evidence", sales)
        self.assertIn("organic-traffic", _APP._registry_role_mandate("SEO Specialist", "Marketing & Brand"))
        self.assertIn("threats", security)
        self.assertIn("creative brief or artifact specification", creative)
        self.assertNotEqual(sales, security)
        self.assertNotEqual(security, creative)
        self.assertIn("human approval", sales)
        self.assertIn("human approval", security)

    def test_growth_roster_roles_receive_specific_mandates(self):
        growth_roles = [role for role in _APP.AGENT_MANDATES if role.startswith("Growth / ")]
        self.assertGreaterEqual(len(growth_roles), 40)
        for role in growth_roles:
            with self.subTest(role=role):
                mandate = _APP.AGENT_MANDATES[role]
                self.assertNotIn("Execute the ", mandate)
                self.assertIn("evidence", mandate.lower())
                self.assertIn("human approval", mandate)

    def test_unknown_role_uses_safe_fallback_mandate(self):
        prompt = _APP._agent_system_prompt("Test-only unknown role")
        self.assertIn(
            "Complete the assigned specialist work using evidence, explicit assumptions, verification, and safe handoffs.",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()
