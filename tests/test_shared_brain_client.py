import json
import unittest
from unittest.mock import patch, MagicMock
from company.shared_brain import SharedBrainClient, SharedBrainError


class SharedBrainClientTests(unittest.TestCase):
    def test_unconfigured_client_fails_before_network(self):
        client = SharedBrainClient(endpoint="https://example.invalid", publishable_key="", access_token="")
        with patch.dict("os.environ", {"SHARED_BRAIN_AGENT_KEY": "", "SUPABASE_PUBLISHABLE_KEY": "", "SUPABASE_ACCESS_TOKEN": ""}, clear=False):
            client.agent_key = ""
            client.publishable_key = ""
            client.access_token = ""
            self.assertFalse(client.configured)
            with self.assertRaisesRegex(SharedBrainError, "needs agent credentials"):
                client.recall()

    def test_machine_auth_headers_and_recall_limit(self):
        client = SharedBrainClient(endpoint="https://example.invalid", timeout=1)
        client.agent_key = "test-only-key"
        client.agent_id = "test-agent"
        body = MagicMock()
        body.__enter__.return_value.read.return_value = json.dumps({"memories": []}).encode()
        with patch("company.shared_brain.urllib.request.urlopen", return_value=body) as urlopen:
            result = client.recall(limit=500)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("X-agent-key"), "test-only-key")
        self.assertEqual(request.get_header("X-agent-id"), "test-agent")
        self.assertEqual(json.loads(request.data)["limit"], 50)
        self.assertEqual(result, [])

    def test_user_session_auth_headers(self):
        client = SharedBrainClient(endpoint="https://example.invalid", publishable_key="pub-test", access_token="user-test")
        client.agent_key = ""
        body = MagicMock()
        body.__enter__.return_value.read.return_value = json.dumps({"memories": []}).encode()
        with patch("company.shared_brain.urllib.request.urlopen", return_value=body) as urlopen:
            client.recall(limit=1)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer user-test")
        self.assertEqual(request.get_header("Apikey"), "pub-test")

    def test_http_error_does_not_leak_response_body(self):
        import urllib.error
        client = SharedBrainClient(endpoint="https://example.invalid")
        client.agent_key = "test-only-key"
        client.agent_id = "test-agent"
        error = urllib.error.HTTPError("https://example.invalid", 401, "Unauthorized", {}, None)
        with patch("company.shared_brain.urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(SharedBrainError, "HTTP 401") as caught:
                client.recall()
        self.assertNotIn("test-only-key", str(caught.exception))

    def test_malformed_recall_response_is_rejected(self):
        client = SharedBrainClient(endpoint="https://example.invalid")
        client.agent_key = "test-only-key"
        body = MagicMock()
        body.__enter__.return_value.read.return_value = json.dumps({"memories": "not-a-list"}).encode()
        with patch("company.shared_brain.urllib.request.urlopen", return_value=body):
            with self.assertRaisesRegex(SharedBrainError, "malformed"):
                client.recall()

    def test_query_is_bounded(self):
        client = SharedBrainClient(endpoint="https://example.invalid")
        client.agent_key = "test-only-key"
        body = MagicMock()
        body.__enter__.return_value.read.return_value = json.dumps({"memories": []}).encode()
        with patch("company.shared_brain.urllib.request.urlopen", return_value=body) as urlopen:
            client.recall(query="q" * 300, limit=0)
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["limit"], 1)
        self.assertEqual(len(payload["query"]), 120)


if __name__ == "__main__":
    unittest.main()
