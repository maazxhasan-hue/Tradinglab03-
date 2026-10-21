"""Regression tests for the deployed Harvey FastAPI worker."""
import os
import tempfile
import unittest
import sys

# Isolate the SQLite database before importing the app (which initializes tables).
_TEST_DIR = tempfile.TemporaryDirectory(prefix="harvey-tests-")
os.environ["DATABASE_PATH"] = os.path.join(_TEST_DIR.name, "harvey-test.db")
os.environ.pop("DATABASE_URL", None)
os.environ["HARVEY_API_KEY"] = "test-only-secret"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
import app as worker


class HarveyWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(worker.app)

    def setUp(self):
        worker.API_KEY = "test-only-secret"

    def test_health_is_public_and_database_is_ready(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "ready")
        self.assertIn(body["database"], {"sqlite", "postgresql"})
        self.assertIn("email_sending", body)

    def test_protected_routes_reject_missing_key(self):
        paths = [
            "/metrics", "/prospects", "/approvals", "/tasks",
            "/agents/status", "/agents/roster", "/company/jobs",
            "/email/status",
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(response.status_code, {401, 503}, response.text)

    def test_protected_metrics_accept_correct_key(self):
        response = self.client.get("/metrics", headers={"X-API-Key": "test-only-secret"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("prospects", response.json())
        self.assertIn("pending_approvals", response.json())

    def test_invalid_discovery_category_is_rejected_before_network_call(self):
        response = self.client.post(
            "/prospects/discover",
            headers={"X-API-Key": "test-only-secret"},
            json={"city": "Bengaluru", "category": "not-a-real-category", "limit": 5},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("Unsupported category", response.json()["detail"])

    def test_agent_runtime_fails_closed_without_provider_credentials(self):
        old_key = os.environ.pop("LLM_API_KEY", None)
        old_model = os.environ.pop("LLM_MODEL", None)
        try:
            response = self.client.post(
                "/agents/run",
                headers={"X-API-Key": "test-only-secret"},
                json={"role": "Testing & QA", "goal": "Review the API access controls."},
            )
            self.assertEqual(response.status_code, 503, response.text)
        finally:
            if old_key is not None:
                os.environ["LLM_API_KEY"] = old_key
            if old_model is not None:
                os.environ["LLM_MODEL"] = old_model


if __name__ == "__main__":
    unittest.main(verbosity=2)
