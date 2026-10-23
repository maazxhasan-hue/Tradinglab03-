from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import private_hq_server  # noqa: E402


class PrivateHQStaticAssetsTests(unittest.TestCase):
    def test_visitor_analytics_page_and_script_are_allowlisted(self) -> None:
        self.assertIn("visitor-analytics.html", private_hq_server.ALLOWED)
        self.assertIn("visitor-analytics-ui.js", private_hq_server.ALLOWED)

    def test_specialist_agent_pages_are_allowlisted_for_authenticated_hq(self) -> None:
        self.assertIn("video-agent.html", private_hq_server.ALLOWED)
        self.assertIn("creative-agent.html", private_hq_server.ALLOWED)
        self.assertIn("inbox.html", private_hq_server.ALLOWED)

    def test_javascript_is_served_with_executable_javascript_mime_type(self) -> None:
        self.assertEqual(
            private_hq_server.content_type_for("visitor-analytics-ui.js"),
            "text/javascript; charset=utf-8",
        )

    def test_html_is_served_with_html_mime_type(self) -> None:
        self.assertEqual(
            private_hq_server.content_type_for("visitor-analytics.html"),
            "text/html; charset=utf-8",
        )

    def test_unknown_file_types_default_to_binary_mime_type(self) -> None:
        self.assertEqual(
            private_hq_server.content_type_for("unexpected.bin"),
            "application/octet-stream",
        )

    def test_analytics_widget_links_to_the_protected_report(self) -> None:
        page = (ROOT / "private-hq" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="./visitor-analytics.html"', page)
        self.assertIn('<script src="./visitor-analytics-ui.js" defer></script>', page)

    def test_full_report_loads_the_same_local_script(self) -> None:
        page = (ROOT / "private-hq" / "visitor-analytics.html").read_text(encoding="utf-8")
        self.assertIn('<script src="./visitor-analytics-ui.js" defer></script>', page)

    def test_private_worker_source_is_not_in_the_static_allowlist(self) -> None:
        self.assertNotIn("../worker/index.js", private_hq_server.ALLOWED)
        self.assertNotIn("worker/index.js", private_hq_server.ALLOWED)


if __name__ == "__main__":
    unittest.main()
