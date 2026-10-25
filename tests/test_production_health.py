import unittest
from unittest.mock import MagicMock, patch

from company.production_health import check_shared_brain
from company.shared_brain import SharedBrainError


class SharedBrainHealthTests(unittest.TestCase):
    @patch("company.shared_brain.SharedBrainClient")
    def test_live_recall_success_returns_metadata_only(self, client_type):
        client = client_type.return_value
        client.configured = True
        client.recall.return_value = [{"summary": "PRIVATE MEMORY MUST NOT LEAK"}]
        result = check_shared_brain()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["operation"], "recall")
        self.assertEqual(result["memory_count"], 1)
        self.assertNotIn("PRIVATE MEMORY MUST NOT LEAK", str(result))

    @patch("company.shared_brain.SharedBrainClient")
    def test_missing_credentials_are_reported_without_network(self, client_type):
        client = client_type.return_value
        client.configured = False
        result = check_shared_brain()
        self.assertEqual(result["status"], "not_configured")
        client.recall.assert_not_called()

    @patch("company.shared_brain.SharedBrainClient")
    def test_auth_failure_is_categorized_without_leaking_response(self, client_type):
        client = client_type.return_value
        client.configured = True
        client.recall.side_effect = SharedBrainError("Shared brain returned HTTP 401.")
        result = check_shared_brain()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["error"], "authentication_rejected")
        self.assertNotIn("HTTP 401", str(result))

    @patch("company.shared_brain.SharedBrainClient")
    def test_rate_limit_is_reported(self, client_type):
        client = client_type.return_value
        client.configured = True
        client.recall.side_effect = SharedBrainError("Shared brain returned HTTP 429.")
        result = check_shared_brain()
        self.assertEqual(result["error"], "rate_limited")


if __name__ == "__main__":
    unittest.main()
