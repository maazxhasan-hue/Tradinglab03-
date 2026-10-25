"""Regression tests for Nexora's bounded batch runner."""
import os
import unittest
from unittest.mock import patch

from company import nexora_batch_executor as runner


class BatchRunnerEnvironmentTests(unittest.TestCase):
    def test_worker_uses_injected_provider_environment(self):
        captured = {}

        def fake_execute(store, task_id, environ=None):
            captured["task_id"] = task_id
            captured["environ"] = dict(environ or {})
            return {"status": "completed"}

        # An injected environment must be honored even if the process environment
        # does not contain a provider key (as in tests and managed worker contexts).
        with patch.dict(os.environ, {}, clear=True), patch.object(
            runner, "execute_agent_draft", side_effect=fake_execute
        ), patch.object(runner, "_wait_for_provider_slot"):
            result = runner._run_one(
                object(), "task-test", environ={"GEMINI_API_KEY": "test-key"}
            )

        self.assertIsNone(result)
        self.assertEqual(captured["task_id"], "task-test")
        self.assertEqual(captured["environ"], {"GEMINI_API_KEY": "test-key"})

    def test_provider_not_configured_is_returned_safely(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            runner, "_wait_for_provider_slot"
        ):
            result = runner._run_one(object(), "task-test", environ={})

        self.assertEqual(result, "ProviderNotConfigured")


if __name__ == "__main__":
    unittest.main()
