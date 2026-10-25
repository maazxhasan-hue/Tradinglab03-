import importlib.util
import unittest
from unittest.mock import patch
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

    def test_timeout_uses_fallback_model_without_repeating_slow_model(self):
        called_models = []

        def fake_run_tool_agent(*, brief, workspace, max_rounds, model):
            called_models.append(model)
            if model == "preferred-model":
                raise RuntimeError("Gemini request failed after retries (TimeoutError).")
            artifact = Path(workspace) / "agent_workspace/specialists/gemini-live-smoke.md"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("GEMINI_NATIVE_TOOL_CALL_OK", encoding="utf-8")
            return {"status": "completed", "tool_calls": 1}

        with (
            patch.dict("os.environ", {
                "GEMINI_API_KEY": "unit-test-key",
                "GEMINI_MODEL": "preferred-model",
                "GEMINI_SMOKE_FALLBACK_MODEL": "fallback-model",
            }, clear=True),
            patch.object(SMOKE, "run_tool_agent", side_effect=fake_run_tool_agent),
            patch.object(SMOKE.time, "sleep") as sleep,
        ):
            self.assertEqual(SMOKE.main(), 0)

        self.assertEqual(called_models, ["preferred-model", "fallback-model"])
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
