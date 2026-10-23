"""Security and smoke tests for the private Nexora HQ routes."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Isolate the backend's SQLite file from the developer's working data.
_TEST_DIR = tempfile.TemporaryDirectory(prefix="nexora-hq-tests-")
os.environ["DATABASE_PATH"] = str(Path(_TEST_DIR.name) / "hq-test.sqlite3")
os.environ["HQ_ADMIN_PASSWORD"] = "test-owner-password"
os.environ["HQ_SESSION_SECRET"] = "test-session-signing-secret-with-sufficient-entropy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harvey-worker"))

try:
    from fastapi.testclient import TestClient
    from hq_app import app, _session_token, _valid_session, _ensure_login_attempts_table
    from app import db
except ModuleNotFoundError as exc:
    # The repository-wide unit-test job intentionally installs only lightweight
    # project dependencies; the dedicated Harvey worker job installs FastAPI.
    if exc.name in {"fastapi", "httpx", "starlette"}:
        raise unittest.SkipTest("Private HQ integration tests require harvey-worker/requirements.txt") from exc
    raise


class PrivateHQTests(unittest.TestCase):
    def setUp(self):
        os.environ["HQ_ADMIN_PASSWORD"] = "test-owner-password"
        os.environ["HQ_SESSION_SECRET"] = "test-session-signing-secret-with-sufficient-entropy"
        self.client = TestClient(app, base_url="https://testserver")
        _ensure_login_attempts_table()
        with db() as conn:
            conn.execute("DELETE FROM hq_login_attempts")

    def tearDown(self):
        self.client.close()
        with db() as conn:
            conn.execute("DELETE FROM hq_login_attempts")

    def test_signed_session_rejects_tampering_and_expiry(self):
        token = _session_token(2000)
        self.assertTrue(_valid_session(token, current_time=1000))
        self.assertFalse(_valid_session(token + "tampered", current_time=1000))
        self.assertFalse(_valid_session(token, current_time=2000))
        self.assertFalse(_valid_session(None, current_time=1000))

    def test_hq_and_overview_are_private_without_session(self):
        page = self.client.get("/hq", follow_redirects=False)
        self.assertEqual(page.status_code, 303)
        self.assertEqual(page.headers["location"], "/hq/login")
        overview = self.client.get("/hq/api/overview")
        self.assertEqual(overview.status_code, 401)

    def test_login_unlocks_hq_and_overview(self):
        response = self.client.post(
            "/hq/login", data={"password": "test-owner-password"}, follow_redirects=False
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/hq")
        cookie = response.headers.get("set-cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=strict", cookie)
        page = self.client.get("/hq")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Company command", page.text)
        overview = self.client.get("/hq/api/overview")
        self.assertEqual(overview.status_code, 200)
        payload = overview.json()
        self.assertIn("tasks", payload)
        self.assertIn("company_jobs", payload)
        self.assertNotIn("input_json", overview.text)
        self.assertNotIn("output_json", overview.text)

    def test_wrong_password_does_not_issue_session(self):
        response = self.client.post(
            "/hq/login", data={"password": "wrong-password"}, follow_redirects=False
        )
        self.assertEqual(response.status_code, 303)
        self.assertIn("error=1", response.headers["location"])
        self.assertNotIn("nexora_hq_session=", response.headers.get("set-cookie", ""))

    def test_login_attempts_are_rate_limited(self):
        for _ in range(8):
            response = self.client.post(
                "/hq/login", data={"password": "wrong-password"}, follow_redirects=False
            )
            self.assertEqual(response.status_code, 303)
        blocked = self.client.post(
            "/hq/login", data={"password": "wrong-password"}, follow_redirects=False
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers.get("retry-after"), "900")

    def test_unconfigured_hq_fails_closed(self):
        old_password = os.environ.pop("HQ_ADMIN_PASSWORD", None)
        try:
            response = self.client.get("/hq/login")
            self.assertEqual(response.status_code, 503)
            self.assertIn("not configured", response.text.lower())
        finally:
            if old_password is not None:
                os.environ["HQ_ADMIN_PASSWORD"] = old_password


if __name__ == "__main__":
    unittest.main()
