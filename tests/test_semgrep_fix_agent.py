import json
import tempfile
import unittest
from pathlib import Path

from company.semgrep_fix_agent import allowed_path, extract_diff, load_findings, validated_provider_base


class SemgrepFixAgentTests(unittest.TestCase):
    def test_allowed_paths_are_backend_only(self):
        self.assertTrue(allowed_path("private_hq_server.py"))
        self.assertTrue(allowed_path("company/agent_runtime.py"))
        self.assertTrue(allowed_path("harvey-worker/app.py"))
        self.assertTrue(allowed_path("tests/test_example.py"))
        self.assertFalse(allowed_path("../.env"))
        self.assertFalse(allowed_path(".github/workflows/semgrep.yml"))
        self.assertFalse(allowed_path("public-site/index.html"))

    def test_provider_base_url_rejects_non_https_and_unapproved_hosts(self):
        self.assertEqual(
            validated_provider_base("https://api.openai.com/v1", "api.openai.com"),
            "https://api.openai.com/v1",
        )
        for unsafe in (
            "file:///etc/passwd",
            "http://api.openai.com/v1",
            "https://127.0.0.1/latest",
            "https://user:pass@api.openai.com/v1",
            "https://api.openai.com/v1?next=file:///etc/passwd",
        ):
            with self.subTest(url=unsafe), self.assertRaises(ValueError):
                validated_provider_base(unsafe, "api.openai.com")

    def test_extract_diff_accepts_only_allowlisted_paths(self):
        patch = (
            "diff --git a/company/example.py b/company/example.py\n"
            "index 1111111..2222222 100644\n"
            "--- a/company/example.py\n"
            "+++ b/company/example.py\n"
            "@@ -1 +1 @@\n"
            "-old = True\n"
            "+new = True\n"
        )
        self.assertIn("diff --git", extract_diff(patch))
        unsafe = patch.replace("company/example.py", ".github/workflows/semgrep.yml")
        with self.assertRaises(ValueError):
            extract_diff(unsafe)

    def test_load_findings_filters_non_backend_files_and_caps_count(self):
        payload = {
            "results": [
                {"path": "public-site/index.html", "check_id": "html.rule",
                 "start": {"line": 1}, "extra": {"severity": "ERROR", "message": "html"}},
                {"path": "harvey-worker/app.py", "check_id": "python.rule",
                 "start": {"line": 10}, "extra": {"severity": "WARNING", "message": "backend"}},
                {"path": "company/agent_runtime.py", "check_id": "python.rule2",
                 "start": {"line": 3}, "extra": {"severity": "INFO", "message": "company"}},
            ]
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "findings.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            findings = load_findings(path, 1)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["path"], "harvey-worker/app.py")


if __name__ == "__main__":
    unittest.main()
