import io
import unittest
from unittest.mock import Mock, patch

import private_hq_server


class CompanyWorkforceRouteTests(unittest.TestCase):
    def make_handler(self, method, path, payload=b""):
        handler = object.__new__(private_hq_server.Handler)
        handler.path = path
        handler.command = method
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.authenticated = lambda: True
        handler.body = Mock()
        return handler

    def test_company_workforce_launch_is_post_only_and_authenticated(self):
        payload = b'{"mission":"Run company workforce integration test"}'
        handler = self.make_handler("POST", "/api/company/agents/start-all", payload)
        with patch.object(private_hq_server, "check_persistent_storage", return_value=(True, {
            "backend": "postgres", "persistent": True, "connection": "ok"
        })), patch.object(private_hq_server, "GrowthStore"), patch.object(
            private_hq_server, "start_company_workforce",
            return_value={"started": True, "roles_assigned": 41, "cycle_id": "test-cycle"},
        ) as launch:
            handler.do_POST()
        launch.assert_called_once()
        self.assertEqual(handler.body.call_args.args[0], 202)

    def test_company_workforce_launch_requires_persistent_postgres(self):
        payload = b'{"mission":"Run company workforce integration test"}'
        handler = self.make_handler("POST", "/api/company/agents/start-all", payload)
        storage = {"backend": "sqlite", "persistent": False, "connection": "not_checked"}
        with patch.object(private_hq_server, "check_persistent_storage", return_value=(False, storage)), patch.object(
            private_hq_server, "start_company_workforce"
        ) as launch:
            handler.do_POST()
        launch.assert_not_called()
        self.assertEqual(handler.body.call_args.args[0], 503)
        response = __import__("json").loads(handler.body.call_args.args[1])
        self.assertEqual(response["error"], "persistent_storage_not_ready")

    def test_growth_batch_launch_requires_persistent_postgres(self):
        handler = self.make_handler("POST", "/api/growth/agents/start-all", b"{}")
        storage = {"backend": "sqlite", "persistent": False, "connection": "not_checked"}
        with patch.object(private_hq_server, "check_persistent_storage", return_value=(False, storage)), patch.object(
            private_hq_server, "start_all_agents"
        ) as launch:
            handler.do_POST()
        launch.assert_not_called()
        self.assertEqual(handler.body.call_args.args[0], 503)

    def test_get_cannot_launch_company_workforce(self):
        handler = self.make_handler("GET", "/api/company/agents/start-all")
        with patch.object(private_hq_server, "GrowthStore"), patch.object(
            private_hq_server, "start_company_workforce"
        ) as launch:
            handler.do_GET()
        launch.assert_not_called()
        self.assertEqual(handler.body.call_args.args[0], 404)

    def test_company_workforce_launch_rejects_unauthenticated_request(self):
        payload = b'{"mission":"Run company workforce integration test"}'
        handler = self.make_handler("POST", "/api/company/agents/start-all", payload)
        handler.authenticated = lambda: False
        with patch.object(private_hq_server, "start_company_workforce") as launch:
            handler.do_POST()
        launch.assert_not_called()
        self.assertEqual(handler.body.call_args.args[0], 401)


if __name__ == "__main__":
    unittest.main()
