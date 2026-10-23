import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harvey-worker"))


class UnifiedWorkforceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        env = {
            "DATABASE_PATH": str(Path(cls._tmp.name) / "harvey-test.sqlite3"),
            "HARVEY_API_KEY": "test-only-key",
            "HQ_SESSION_SECRET": "test-session-secret-for-tests-only",
            "HQ_ADMIN_PASSWORD": "test-only-password",
        }
        cls._env_patch = patch.dict(os.environ, env)
        cls._env_patch.start()
        try:
            import fastapi  # noqa: F401
        except ImportError:
            cls._env_patch.stop()
            raise unittest.SkipTest("Harvey integration dependencies are not installed in this test environment.")
        import app as harvey_app
        cls.app = harvey_app

    @classmethod
    def tearDownClass(cls):
        cls._env_patch.stop()
        cls._tmp.cleanup()

    def test_every_department_role_is_registered_for_execution(self):
        registry = json.loads((ROOT / "company" / "roles.json").read_text(encoding="utf-8"))
        expected = {
            role.strip()
            for department in registry
            for role in department.get("roles", [])
            if isinstance(role, str) and role.strip()
        }
        self.assertTrue(expected)
        self.assertTrue(expected.issubset(set(self.app.AGENT_MANDATES)))
        self.assertTrue(expected.issubset(self.app.AGENT_ROLES))

    def test_all_41_growth_roles_are_registered_in_harvey_roster(self):
        from company.nexora_growth_runtime import AGENTS
        expected = {"Growth / " + agent["name"] for agent in AGENTS}
        self.assertEqual(len(expected), 41)
        self.assertTrue(expected.issubset(set(self.app.AGENT_MANDATES)))
        self.assertTrue(expected.issubset(self.app.AGENT_ROLES))

    def test_live_hq_exposes_authenticated_company_workforce_routes(self):
        import hq_app
        paths = {route.path for route in hq_app.app.routes}
        self.assertIn("/hq/api/company-workforce", paths)
        self.assertIn("/hq/api/company-workforce/start", paths)

    def test_openrouter_free_model_identifier_is_valid(self):
        from company.nexora_agent_executor import _validated_model
        self.assertEqual(_validated_model("openrouter/free"), "openrouter/free")

    def test_wider_company_role_can_create_a_persistent_task(self):
        from company.nexora_growth_runtime import COMPANY_AGENTS, GrowthStore
        store = GrowthStore(Path(self._tmp.name) / "growth-test.sqlite3")
        agent = COMPANY_AGENTS[0]
        task = store.create_task("Registry integration test", agent["agent_id"], {"mode": "test"})
        self.assertEqual(task["agent_id"], agent["agent_id"])
        self.assertEqual(task["status"], "queued")

    def test_queue_recovery_fails_closed_without_provider_credentials(self):
        from company.nexora_batch_executor import resume_queued_tasks
        from company.nexora_growth_runtime import GrowthStore
        store = GrowthStore(Path(self._tmp.name) / "recovery-test.sqlite3")
        result = resume_queued_tasks(store, environ={})
        self.assertFalse(result["started"])
        self.assertEqual(result["reason"], "provider_not_configured")

    def test_company_dispatch_has_background_execution_and_restart_recovery(self):
        self.assertTrue(callable(self.app._run_company_cycle))
        self.assertTrue(callable(self.app._company_cycle_supervisor))
        self.assertIn(self.app._start_company_cycle_supervisor, self.app.app.router.on_startup)


if __name__ == "__main__":
    unittest.main()
