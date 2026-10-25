import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("gemini_tool_agent_live_smoke.py")
SPEC = importlib.util.spec_from_file_location("gemini_tool_agent_live_smoke_under_test", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load Gemini live smoke helpers")
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


class GeminiSmokeRetryTests(unittest.TestCase):
    def test_raw_and_wrapped_timeouts_are_transient(self):
        self.assertTrue(SMOKE.is_timeout_error(TimeoutError("read timed out")))
        wrapped = RuntimeError("Gemini request failed after retries (TimeoutError).")
        self.assertTrue(SMOKE.is_timeout_error(wrapped))
        self.assertTrue(SMOKE.is_transient_provider_error(wrapped))

    def test_capacity_errors_are_transient(self):
        for message in (
            "Gemini returned HTTP 429",
            "Gemini returned HTTP 503",
            "Provider is under high demand",
        ):
            with self.subTest(message=message):
                self.assertTrue(SMOKE.is_transient_provider_error(RuntimeError(message)))

    def test_auth_and_request_errors_are_not_transient(self):
        for message in (
            "Gemini returned HTTP 400: Invalid JSON payload",
            "Gemini returned HTTP 401",
            "Unsupported model name",
        ):
            with self.subTest(message=message):
                self.assertFalse(SMOKE.is_transient_provider_error(RuntimeError(message)))


if __name__ == "__main__":
    unittest.main()
