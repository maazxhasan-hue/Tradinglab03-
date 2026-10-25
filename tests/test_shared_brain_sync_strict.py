"""Regression tests for strict shared-brain workflow synchronization."""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

from company import shared_brain_sync
from company.shared_brain import SharedBrainError


class SharedBrainSyncStrictTests(unittest.TestCase):
    def _argv(self) -> list[str]:
        return [
            "shared_brain_sync",
            "--status", "success",
            "--run-id", "12345",
            "--commit", "abc123",
            "--workflow", "Unit Test",
            "--repository", "owner/repo",
        ]

    def test_successful_write_returns_zero_in_strict_mode(self) -> None:
        with patch.dict(os.environ, {"SHARED_BRAIN_AGENT_ID": "test-agent", "SHARED_BRAIN_STRICT": "1"}):
            with patch.object(sys, "argv", self._argv()):
                with patch.object(shared_brain_sync, "SharedBrainClient") as client_cls:
                    client_cls.return_value.remember.return_value = {"saved": True, "scope": "shared"}
                    client_cls.return_value.recall.return_value = [{"memory_key": "Unit-Test:12345", "content": {"run_id": "12345"}}]
                    self.assertEqual(shared_brain_sync.main(), 0)
                    client_cls.return_value.recall.assert_called_once_with(project_key="nexora", namespace="agent-runs", query="run 12345", limit=50)

    def test_failed_write_returns_nonzero_in_strict_mode(self) -> None:
        with patch.dict(os.environ, {"SHARED_BRAIN_AGENT_ID": "test-agent", "SHARED_BRAIN_STRICT": "1"}):
            with patch.object(sys, "argv", self._argv()):
                with patch.object(shared_brain_sync, "SharedBrainClient") as client_cls:
                    client_cls.return_value.remember.side_effect = SharedBrainError("unavailable")
                    self.assertEqual(shared_brain_sync.main(), 1)

    def test_failed_readback_returns_nonzero_in_strict_mode(self) -> None:
        with patch.dict(os.environ, {"SHARED_BRAIN_AGENT_ID": "test-agent", "SHARED_BRAIN_STRICT": "1"}):
            with patch.object(sys, "argv", self._argv()):
                with patch.object(shared_brain_sync, "SharedBrainClient") as client_cls:
                    client_cls.return_value.remember.return_value = {"saved": True, "scope": "shared"}
                    client_cls.return_value.recall.return_value = []
                    self.assertEqual(shared_brain_sync.main(), 1)

    def test_failed_write_preserves_non_strict_compatibility(self) -> None:
        with patch.dict(os.environ, {"SHARED_BRAIN_AGENT_ID": "test-agent"}):
            os.environ.pop("SHARED_BRAIN_STRICT", None)
            with patch.object(sys, "argv", self._argv()):
                with patch.object(shared_brain_sync, "SharedBrainClient") as client_cls:
                    client_cls.return_value.remember.side_effect = SharedBrainError("unavailable")
                    self.assertEqual(shared_brain_sync.main(), 0)


if __name__ == "__main__":
    unittest.main()
