import io
import json
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

from company.pocketpal_connector import LocalModelError, chat_completion


class PocketPalConnectorTests(unittest.TestCase):
    def _response(self, payload):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps(payload).encode("utf-8")
        return response

    def test_private_openai_compatible_server_text_completion(self):
        response = self._response({"choices": [{"message": {"content": "Local reply"}}]})
        with patch.dict("os.environ", {
            "TRADINGLAB03_LOCAL_MODEL_URL": "http://192.168.1.25:8080",
            "TRADINGLAB03_LOCAL_MODEL_NAME": "qwen-local",
            "TRADINGLAB03_LOCAL_MODEL_TOKEN": "test-token",
        }, clear=True), patch(
            "company.pocketpal_connector.urllib.request.urlopen", return_value=response
        ) as urlopen:
            result = chat_completion([{"role": "user", "content": "Explain this error"}])
        self.assertEqual(result, {
            "model": "qwen-local", "content": "Local reply", "provider": "private_local"
        })
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://192.168.1.25:8080/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertFalse(json.loads(request.data)["stream"])

    def test_public_ip_is_rejected_before_network_call(self):
        with patch("company.pocketpal_connector.urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(ValueError, "private"):
                chat_completion([{"role": "user", "content": "hello"}],
                                base_url="http://8.8.8.8:8080")
        urlopen.assert_not_called()

    def test_dns_hostname_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "DNS hostnames"):
            chat_completion([{"role": "user", "content": "hello"}],
                            base_url="http://model.example:8080")

    def test_rejects_tool_or_invalid_roles(self):
        with self.assertRaisesRegex(ValueError, "messages must"):
            chat_completion([{"role": "tool", "content": "run command"}],
                            base_url="http://127.0.0.1:8080")

    def test_http_error_does_not_leak_server_body(self):
        error = urllib.error.HTTPError(
            "http://127.0.0.1:8080/v1/chat/completions", 500, "error", {},
            io.BytesIO(b'{"error":"private prompt or token"}'),
        )
        with patch("company.pocketpal_connector.urllib.request.urlopen", side_effect=error):
            with self.assertRaises(LocalModelError) as raised:
                chat_completion([{"role": "user", "content": "hello"}],
                                base_url="http://127.0.0.1:8080")
        self.assertEqual(str(raised.exception), "Local model server returned HTTP 500.")
        self.assertNotIn("private prompt", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
