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
        with patch.object(private_hq_server, "GrowthStore"), patch.object(
            private_hq_server, "start_company_workforce",
            return_value={"started": True, "roles_assigned": 41, "cycle_id": "test-cycle"},
        ) as launch:
            handler.do_POST()
        launch.assert_called_once()
        self.assertEqual(handler.body.call_args.args[0], 202)

    def test_get_cannot_launch_company_workforce(self):
        handler = self.make_handler("GET", "/api/company/agents/start-all")
        with patch.object(private_hq_server, "start_company_workforce") as launch:
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
