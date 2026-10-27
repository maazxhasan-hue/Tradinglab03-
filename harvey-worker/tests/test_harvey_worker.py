"""Regression tests for the deployed Harvey FastAPI worker."""
import os
import tempfile
import unittest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

# Isolate the SQLite database before importing the app (which initializes tables).
_TEST_DIR = tempfile.TemporaryDirectory(prefix="harvey-tests-")
os.environ["DATABASE_PATH"] = os.path.join(_TEST_DIR.name, "harvey-test.db")
os.environ.pop("DATABASE_URL", None)
os.environ["HARVEY_API_KEY"] = "test-only-secret"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
import app as worker
import hq_app as hq


class HarveyWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(worker.app)
        cls.hq_client = TestClient(worker.app, base_url="https://testserver")

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.hq_client.close()

    def setUp(self):
        worker.API_KEY = "test-only-secret"
        os.environ["HQ_ADMIN_PASSWORD"] = "test-owner-password"
        os.environ["HQ_SESSION_SECRET"] = "test-session-signing-secret-with-sufficient-entropy"
        hq._ensure_login_attempts_table()
        with worker.db() as conn:
            conn.execute("DELETE FROM hq_login_attempts")

    def test_health_is_public_and_database_is_ready(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "ready")
        self.assertIn(body["database"], {"sqlite", "postgresql"})
        self.assertIn("email_sending", body)

    def test_root_health_landing_is_available(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["health"], "/health")

    def test_root_health_probe_accepts_head(self):
        response = self.client.head("/")
        self.assertEqual(response.status_code, 200, response.text)

    def test_project_builder_fails_closed_without_model_credentials(self):
        names = ("LLM_API_KEY", "LLM_MODEL", "OPENAI_API_KEY", "OPENAI_MODEL")
        previous = {name: os.environ.pop(name, None) for name in names}
        try:
            response = self.client.post(
                "/projects/build",
                headers={"X-API-Key": "test-only-secret"},
                json={"name": "Test project", "brief": "Build a small test project with a README and tests."},
            )
            self.assertEqual(response.status_code, 503, response.text)
        finally:
            for name, value in previous.items():
                if value is not None:
                    os.environ[name] = value

    def test_openai_compatibility_environment_configures_agent_runtime(self):
        names = ("LLM_API_KEY", "LLM_MODEL", "OPENAI_API_KEY", "OPENAI_MODEL")
        previous = {name: os.environ.pop(name, None) for name in names}
        os.environ["OPENAI_API_KEY"] = "test-provider-key"
        os.environ["OPENAI_MODEL"] = "gpt-4.1-mini"
        try:
            response = self.client.get("/agents/status", headers={"X-API-Key": "test-only-secret"})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()["model_configured"])
            self.assertEqual(response.json()["model"], "gpt-4.1-mini")
        finally:
            for name in names:
                os.environ.pop(name, None)
            for name, value in previous.items():
                if value is not None:
                    os.environ[name] = value

    def test_protected_routes_reject_missing_key(self):
        paths = [
            "/metrics", "/prospects", "/approvals", "/tasks",
            "/agents/status", "/company/jobs",
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

    def test_hq_redirects_and_api_rejects_unauthenticated_requests(self):
        page = self.hq_client.get("/hq", follow_redirects=False)
        self.assertEqual(page.status_code, 303)
        self.assertEqual(page.headers["location"], "/hq/login")
        overview = self.hq_client.get("/hq/api/overview")
        self.assertEqual(overview.status_code, 401)

    def test_hq_login_shows_live_sanitized_overview_and_logout(self):
        response = self.hq_client.post(
            "/hq/login", data={"password": "test-owner-password"}, follow_redirects=False
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/hq")
        cookie = response.headers.get("set-cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=strict", cookie)
        page = self.hq_client.get("/hq")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Company command", page.text)
        overview = self.hq_client.get("/hq/api/overview")
        self.assertEqual(overview.status_code, 200, overview.text)
        self.assertIn("company_jobs", overview.json())
        self.assertNotIn("input_json", overview.text)
        self.assertNotIn("output_json", overview.text)
        self.hq_client.post("/hq/logout", follow_redirects=False)
        self.assertEqual(self.hq_client.get("/hq", follow_redirects=False).status_code, 303)

    def test_hq_wrong_password_is_rate_limited_and_does_not_unlock(self):
        for _ in range(8):
            response = self.hq_client.post(
                "/hq/login", data={"password": "wrong-password"}, follow_redirects=False
            )
            self.assertEqual(response.status_code, 303)
        blocked = self.hq_client.post(
            "/hq/login", data={"password": "wrong-password"}, follow_redirects=False
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers.get("retry-after"), "900")
        self.assertEqual(self.hq_client.get("/hq", follow_redirects=False).status_code, 303)

    def test_hq_fails_closed_without_password_configuration(self):
        previous = os.environ.pop("HQ_ADMIN_PASSWORD", None)
        try:
            response = self.hq_client.get("/hq/login")
            self.assertEqual(response.status_code, 503)
        finally:
            if previous is not None:
                os.environ["HQ_ADMIN_PASSWORD"] = previous

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


    def test_shared_brain_proxy_rejects_missing_or_wrong_secret(self):
        with patch.object(worker, "SHARED_BRAIN_PROXY_KEY", "proxy-test-secret"):
            missing = self.client.post(
                "/internal/shared-brain-proxy",
                json={"action": "recall", "project_key": "nexora", "namespace": "company"},
            )
            wrong = self.client.post(
                "/internal/shared-brain-proxy",
                headers={"X-Brain-Proxy-Key": "wrong", "X-Agent-Id": "tradinglab03"},
                json={"action": "recall", "project_key": "nexora", "namespace": "company"},
            )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)

    def test_shared_brain_proxy_limits_scope_and_forwards_authenticated_recall(self):
        expected = {"memories": [{"memory_key": "smoke"}], "count": 1, "scope": "shared-agent"}
        with patch.object(worker, "SHARED_BRAIN_PROXY_KEY", "proxy-test-secret"), patch.object(
            worker, "shared_brain_request", return_value=expected
        ) as call:
            denied = self.client.post(
                "/internal/shared-brain-proxy",
                headers={"X-Brain-Proxy-Key": "proxy-test-secret", "X-Agent-Id": "tradinglab03"},
                json={"action": "recall", "project_key": "other", "namespace": "company"},
            )
            allowed = self.client.post(
                "/internal/shared-brain-proxy",
                headers={"X-Brain-Proxy-Key": "proxy-test-secret", "X-Agent-Id": "tradinglab03"},
                json={"action": "recall", "project_key": "nexora", "namespace": "company", "query": "agent test", "limit": 2},
            )
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertEqual(allowed.json(), expected)
        call.assert_called_once_with(
            {"action": "recall", "project_key": "nexora", "namespace": "company", "query": "agent test", "limit": 2},
            agent_id="tradinglab03",
        )

    def test_shared_brain_proxy_remember_uses_authenticated_agent_identity(self):
        expected = {"saved": True, "scope": "shared-agent"}
        payload = {
            "action": "remember", "project_key": "nexora", "namespace": "company",
            "memory_key": "test-run-1", "source_agent": "spoofed-agent",
            "summary": "internal smoke", "content": {"status": "completed"}, "tags": ["smoke"],
        }
        with patch.object(worker, "SHARED_BRAIN_PROXY_KEY", "proxy-test-secret"), patch.object(
            worker, "shared_brain_request", return_value=expected
        ) as call:
            response = self.client.post(
                "/internal/shared-brain-proxy",
                headers={"X-Brain-Proxy-Key": "proxy-test-secret", "X-Agent-Id": "tradinglab03"},
                json=payload,
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)
        forwarded = call.call_args.args[0]
        self.assertEqual(forwarded["source_agent"], "tradinglab03")
        self.assertNotEqual(forwarded["source_agent"], "spoofed-agent")

    def test_internal_agent_smoke_rejects_missing_or_wrong_auth(self):
        missing = self.client.post("/internal/agent-smoke")
        self.assertEqual(missing.status_code, 401, missing.text)
        wrong_scheme = self.client.post(
            "/internal/agent-smoke", headers={"Authorization": "Basic not-a-token"}
        )
        self.assertEqual(wrong_scheme.status_code, 401, wrong_scheme.text)

    def test_github_oidc_smoke_identity_is_locked_to_the_main_workflow(self):
        import jwt

        signing_key = MagicMock()
        signing_key.key = object()
        allowed_claims = {
            "sub": "repo:maazxhasan-hue/Tradinglab03-:environment:internal-smoke",
            "repository": "maazxhasan-hue/Tradinglab03-",
            "ref": "refs/heads/main",
            "workflow_ref": "maazxhasan-hue/Tradinglab03-/.github/workflows/agent-live-verification.yml@refs/heads/main",
            "event_name": "push",
        }
        with patch("jwt.PyJWKClient") as jwks_factory, patch(
            "jwt.decode", return_value=allowed_claims
        ) as decode:
            jwks_factory.return_value.get_signing_key_from_jwt.return_value = signing_key
            result = worker._verify_github_actions_smoke_identity("synthetic-signed-token")
        self.assertEqual(result, allowed_claims)
        self.assertEqual(decode.call_args.kwargs["audience"], "nexora-harvey-agent-smoke")
        self.assertEqual(decode.call_args.kwargs["issuer"], "https://token.actions.githubusercontent.com")

        denied_claims = dict(allowed_claims, workflow_ref="attacker/workflow.yml@refs/heads/main")
        with patch("jwt.PyJWKClient") as jwks_factory, patch(
            "jwt.decode", return_value=denied_claims
        ):
            jwks_factory.return_value.get_signing_key_from_jwt.return_value = signing_key
            with self.assertRaises(HTTPException) as error:
                worker._verify_github_actions_smoke_identity("synthetic-signed-token")
        self.assertEqual(error.exception.status_code, 403)

    def test_internal_agent_smoke_invokes_only_fixed_safe_specialist_task(self):
        expected = {
            "task_id": 123,
            "role": "Knowledge & Memory",
            "status": "completed",
            "output": "NEXORA_AGENT_EXECUTION_OK",
            "shared_brain": {"recall_count": 1, "remembered": True},
        }
        with patch.object(worker, "_verify_github_actions_smoke_identity") as verify, patch.object(
            worker, "run_agent", new_callable=AsyncMock, return_value=expected
        ) as run_agent:
            response = self.client.post(
                "/internal/agent-smoke",
                headers={"Authorization": "Bearer synthetic-oidc-token"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), expected)
        verify.assert_called_once_with("synthetic-oidc-token")
        request = run_agent.await_args.args[0]
        self.assertEqual(request.role, "Knowledge & Memory")
        self.assertIn("NEXORA_AGENT_EXECUTION_OK", request.goal)
        self.assertIn("Do not perform external actions", request.constraints)
        self.assertEqual(run_agent.await_args.kwargs["x_api_key"], "test-only-secret")


    def test_agent_recall_failure_records_terminal_failed_task(self):
        names = ("OPENROUTER_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY")
        previous = {name: os.environ.pop(name, None) for name in names}
        os.environ["OPENAI_API_KEY"] = "test-provider-key"
        try:
            with patch.object(worker, "_shared_brain_configured", return_value=True), \\
                 patch.object(worker, "shared_brain_recall", side_effect=RuntimeError("synthetic recall failure")):
                response = self.client.post(
                    "/agents/run",
                    headers={"X-API-Key": "test-only-secret"},
                    json={"role": "Knowledge & Memory", "goal": "Test recall failure task status."},
                )
            self.assertEqual(response.status_code, 503, response.text)
            with worker.db() as conn:
                row = conn.execute(
                    "SELECT status,error FROM tasks WHERE kind=? ORDER BY id DESC LIMIT 1",
                    ("agent:Knowledge & Memory",),
                ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "failed")
            self.assertIn("Shared Brain recall failed", row["error"])
        finally:
            for name in names:
                os.environ.pop(name, None)
            for name, value in previous.items():
                if value is not None:
                    os.environ[name] = value


if __name__ == "__main__":
    unittest.main(verbosity=2)
