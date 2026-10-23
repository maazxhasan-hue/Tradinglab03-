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
import hq_app as hq
import pricing_service as pricing


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
        self.hq_client.cookies.clear()
        hq._ensure_login_attempts_table()
        pricing.ensure_pricing_tables()
        with worker.db() as conn:
            conn.execute("DELETE FROM hq_login_attempts")
            conn.execute("DELETE FROM pricing_audit_log")
            conn.execute("DELETE FROM pricing_items")

    def login_hq(self):
        response = self.hq_client.post(
            "/hq/login", data={"password": "test-owner-password"}, follow_redirects=False
        )
        self.assertEqual(response.status_code, 303)

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
        pricing_page = self.hq_client.get("/hq/pricing")
        self.assertEqual(pricing_page.status_code, 200, pricing_page.text)
        self.assertIn("Pricing management", pricing_page.text)
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

    def test_pricing_management_is_private_but_public_catalog_is_safe(self):
        self.assertEqual(self.hq_client.get("/hq/pricing", follow_redirects=False).status_code, 303)
        self.assertEqual(self.hq_client.get("/hq/api/pricing").status_code, 401)
        public = self.hq_client.get("/public/pricing")
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.json()["items"], [])

    def test_pricing_draft_publish_edit_and_audit_flow(self):
        self.login_hq()
        payload = {
            "title": "Starter Automation", "slug": "starter-automation",
            "category": "service", "description": "Setup and support",
            "amount_inr": "9999.00", "billing_period": "one_time",
            "discount_percent": "10", "promo_price_inr": "8999.00",
        }
        created = self.hq_client.post("/hq/api/pricing", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        item = created.json()
        item_id = item["id"]
        self.assertEqual(item["status"], "draft")
        self.assertEqual(item["amount_inr"], "9999.00")
        self.assertEqual(self.hq_client.get("/public/pricing").json()["items"], [])

        published = self.hq_client.post(f"/hq/api/pricing/{item_id}/publish", json={})
        self.assertEqual(published.status_code, 200, published.text)
        self.assertTrue(published.json()["published"])
        live = self.hq_client.get("/public/pricing").json()["items"]
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0]["title"], "Starter Automation")
        self.assertEqual(live[0]["amount_inr"], "9999.00")

        changed = dict(payload, title="Starter Automation Plus", slug="starter-automation-plus", amount_inr="12999.00")
        updated = self.hq_client.put(f"/hq/api/pricing/{item_id}", json=changed)
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertTrue(updated.json()["has_unpublished_changes"])
        live_before_publish = self.hq_client.get("/public/pricing").json()["items"][0]
        self.assertEqual(live_before_publish["title"], "Starter Automation")
        self.assertEqual(live_before_publish["slug"], "starter-automation")
        self.assertEqual(live_before_publish["amount_inr"], "9999.00")

        republished = self.hq_client.post(f"/hq/api/pricing/{item_id}/publish", json={})
        self.assertEqual(republished.status_code, 200, republished.text)
        live_after_publish = self.hq_client.get("/public/pricing").json()["items"][0]
        self.assertEqual(live_after_publish["title"], "Starter Automation Plus")
        self.assertEqual(live_after_publish["slug"], "starter-automation-plus")
        self.assertEqual(live_after_publish["amount_inr"], "12999.00")
        history = self.hq_client.get(f"/hq/api/pricing/{item_id}/history")
        self.assertEqual(history.status_code, 200, history.text)
        events = [entry["event"] for entry in history.json()["items"]]
        self.assertIn("created_draft", events)
        self.assertIn("published", events)
        self.assertIn("published_item_draft_updated", events)

    def test_client_specific_quotes_never_appear_in_public_catalog(self):
        self.login_hq()
        payload = {
            "title": "Private Client Quote", "slug": "private-client-quote",
            "category": "client_quote", "description": "Confidential bespoke scope",
            "amount_inr": "25000.00", "billing_period": "custom",
            "discount_percent": "0", "promo_price_inr": None,
        }
        created = self.hq_client.post("/hq/api/pricing", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        item_id = created.json()["id"]
        self.assertEqual(self.hq_client.post(f"/hq/api/pricing/{item_id}/publish", json={}).status_code, 200)
        self.assertEqual(self.hq_client.get("/public/pricing").json()["items"], [])
        private_list = self.hq_client.get("/hq/api/pricing")
        self.assertIn("Private Client Quote", [item["title"] for item in private_list.json()["items"]])

    def test_pricing_validation_rejects_invalid_slug_and_promotion(self):
        self.login_hq()
        base = {
            "title": "Invalid Promotion", "slug": "invalid-promotion",
            "category": "subscription", "description": "",
            "amount_inr": "1000.00", "billing_period": "monthly",
            "discount_percent": "0", "promo_price_inr": "1000.00",
        }
        response = self.hq_client.post("/hq/api/pricing", json=base)
        self.assertEqual(response.status_code, 422, response.text)
        bad_slug = dict(base, slug="../bad", promo_price_inr=None)
        response = self.hq_client.post("/hq/api/pricing", json=bad_slug)
        self.assertEqual(response.status_code, 422, response.text)
        too_precise = dict(base, slug="too-precise", promo_price_inr=None, amount_inr="1.001")
        response = self.hq_client.post("/hq/api/pricing", json=too_precise)
        self.assertEqual(response.status_code, 422, response.text)

    def test_duplicate_pricing_slug_is_rejected_and_archive_unpublishes(self):
        self.login_hq()
        payload = {
            "title": "Monthly Assistant", "slug": "monthly-assistant",
            "category": "subscription", "description": "Monthly plan",
            "amount_inr": "499.00", "billing_period": "monthly",
            "discount_percent": "0", "promo_price_inr": None,
        }
        created = self.hq_client.post("/hq/api/pricing", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        duplicate = self.hq_client.post("/hq/api/pricing", json=dict(payload, title="Another plan"))
        self.assertEqual(duplicate.status_code, 422, duplicate.text)
        item_id = created.json()["id"]
        self.assertEqual(self.hq_client.post(f"/hq/api/pricing/{item_id}/publish", json={}).status_code, 200)
        archived = self.hq_client.post(f"/hq/api/pricing/{item_id}/archive", json={})
        self.assertEqual(archived.status_code, 200, archived.text)
        self.assertEqual(self.hq_client.get("/public/pricing").json()["items"], [])
        events = self.hq_client.get(f"/hq/api/pricing/{item_id}/history").json()["items"]
        self.assertIn("archived", [entry["event"] for entry in events])

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
