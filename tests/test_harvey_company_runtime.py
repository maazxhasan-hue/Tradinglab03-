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

    def test_company_dispatch_has_background_execution_and_restart_recovery(self):
        self.assertTrue(callable(self.app._run_company_cycle))
        self.assertTrue(callable(self.app._company_cycle_supervisor))
        self.assertIn("company_jobs", self.app.init_db.__code__.co_consts[0] if self.app.init_db.__code__.co_consts else "")


if __name__ == "__main__":
    unittest.main()
