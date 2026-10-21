import json
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


    def test_gemini_native_provider_uses_key_header_and_parses_response(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Draft complete."}]}}]
        }).encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict("os.environ", {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "test-secret"}, clear=True), \
             patch("company.tool_agent.urllib.request.urlopen", return_value=response) as urlopen:
            result = run_tool_agent(brief={"business_name": "Example"}, workspace=tmp, max_rounds=1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["final_message"], "Draft complete.")
        request = urlopen.call_args.args[0]
        self.assertIn(":generateContent", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-secret")
        self.assertNotIn("test-secret", request.full_url)

    def test_gemini_native_provider_skips_without_key(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"AI_PROVIDER": "gemini"}, clear=True):
            result = run_tool_agent(brief={"business_name": "Example"}, workspace=tmp)
        self.assertEqual(result["status"], "skipped_no_api_key")


if __name__ == "__main__":
    unittest.main()
