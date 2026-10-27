import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

SCRIPT = Path(__file__).with_name("harvey_agent_live_smoke.py")
SPEC = importlib.util.spec_from_file_location("harvey_agent_live_smoke_under_test", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load live smoke script")
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


def fake_response(payload):
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return response


class HarveyAgentLiveSmokeTests(unittest.TestCase):
    def test_missing_key_fails_without_network(self):
        with patch.dict("os.environ", {}, clear=True), \
             patch.object(SMOKE.urllib.request, "urlopen") as urlopen:
            self.assertEqual(SMOKE.main(), 1)
        urlopen.assert_not_called()

    def test_success_requires_completion_and_shared_brain_writeback(self):
        payload = {
            "task_id": "synthetic-task-id",
            "role": "Knowledge & Memory",
            "status": "completed",
            "output": "NEXORA_AGENT_EXECUTION_OK",
            "shared_brain": {"recall_count": 1, "remembered": True},
        }
        response = fake_response(payload)
        with (
            patch.dict("os.environ", {
                "HARVEY_API_KEY": "unit-test-key",
                "HARVEY_WORKER_URL": "https://harvey.example.invalid",
            }, clear=True),
            patch.object(SMOKE.urllib.request, "urlopen", return_value=response) as urlopen,
        ):
            self.assertEqual(SMOKE.main(), 0)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://harvey.example.invalid/agents/run")
        self.assertEqual(request.get_header("X-api-key"), "unit-test-key")
        self.assertNotIn("unit-test-key", request.full_url)

    def test_http_error_body_is_not_printed(self):
        error = urllib.error.HTTPError(
            "https://harvey.example.invalid/agents/run",
            503,
            "Service Unavailable",
            {},
            io.BytesIO(b"secret response body"),
        )
        with (
            patch.dict("os.environ", {"HARVEY_API_KEY": "unit-test-key"}, clear=True),
            patch.object(SMOKE.urllib.request, "urlopen", side_effect=error),
        ):
            from contextlib import redirect_stdout
            import io as io_module
            output = io_module.StringIO()
            with redirect_stdout(output):
                self.assertEqual(SMOKE.main(), 1)
        self.assertNotIn("secret response body", output.getvalue())
        self.assertNotIn("unit-test-key", output.getvalue())
        self.assertIn("HTTP 503", output.getvalue())


if __name__ == "__main__":
    unittest.main()
