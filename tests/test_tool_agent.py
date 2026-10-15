import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company.tool_agent import execute_tool, run_tool_agent


class ToolAgentTests(unittest.TestCase):
    def test_write_and_read_artifact_within_allowed_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = execute_tool("write_artifact", {
                "path": "agent_workspace/notes.md", "content": "Implemented draft"
            }, tmp)
            self.assertEqual(result["written"], "agent_workspace/notes.md")
            read = execute_tool("read_artifact", {"path": "agent_workspace/notes.md"}, tmp)
            self.assertEqual(read["content"], "Implemented draft")

    def test_write_blocks_path_traversal_and_protected_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in ("../outside.md", "agent_workspace/../outside.md",
                         "delivery_bundle/website/quality_report.json",
                         "random/place.md", "agent_workspace/run.sh"):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        execute_tool("write_artifact", {"path": path, "content": "x"}, tmp)

    def test_read_blocks_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                execute_tool("read_artifact", {"path": "../secret.txt"}, tmp)

    def test_no_key_skips_model_without_blocking_deterministic_work(self):
        with patch.dict("os.environ", {}, clear=True):
            result = run_tool_agent(brief={"business_name": "Example"}, workspace=tempfile.mkdtemp(), api_key="")
        self.assertEqual(result["status"], "skipped_no_api_key")
        self.assertEqual(result["tool_calls"], 0)

    def test_unknown_tool_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not allowlisted"):
                execute_tool("run_shell", {"command": "whoami"}, tmp)


if __name__ == "__main__":
    unittest.main()
