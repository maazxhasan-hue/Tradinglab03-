import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company import daily_company_review


class DailyCompanyReviewTests(unittest.TestCase):
    def test_prioritizes_only_explicit_active_direct_client_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leads_file = root / "data" / "leads.json"
            out_file = root / "data" / "opportunities" / "daily-company-review.md"
            leads_file.parent.mkdir(parents=True)
            leads_file.write_text(json.dumps({"leads": [
                {"business_name": "Low priority client", "opportunity_type": "client_project",
                 "client_fit": True, "opportunity_priority": "low", "opportunity_score": 10,
                 "status": "new", "source_url": "https://example.com/low",
                 "next_action": "Verify listing"},
                {"business_name": "High priority client", "opportunity_type": "client_project",
                 "client_fit": True, "opportunity_priority": "high", "opportunity_score": 80,
                 "status": "new", "source_url": "https://example.com/high",
                 "next_action": "Review fit"},
                {"business_name": "Employment role", "opportunity_type": "employment_role",
                 "client_fit": False, "opportunity_priority": "high", "opportunity_score": 99,
                 "status": "new", "source_url": "https://example.com/job"},
                {"business_name": "Legacy unclassified", "opportunity_priority": "high",
                 "opportunity_score": 100, "status": "new",
                 "source_url": "https://example.com/legacy"},
                {"business_name": "Closed client", "opportunity_type": "client_project",
                 "client_fit": True, "opportunity_priority": "high", "opportunity_score": 95,
                 "status": "lost", "source_url": "https://example.com/closed"},
                {"business_name": "Malformed score", "opportunity_type": "client_project",
                 "client_fit": True, "opportunity_priority": "medium",
                 "opportunity_score": "not-a-number", "status": "new"},
            ]}), encoding="utf-8")
            with patch.object(daily_company_review, "ROOT", root), \
                 patch.object(daily_company_review, "LEADS_FILE", leads_file), \
                 patch.object(daily_company_review, "OUT_FILE", out_file):
                self.assertEqual(daily_company_review.main(), 0)
            report = out_file.read_text(encoding="utf-8")
            self.assertIn("Total tracked records: 6", report)
            self.assertIn("Direct client-project candidates (explicit buyer intent): 3", report)
            queue = report.split("## Highest-priority direct client-project queue", 1)[1].split("## Historical", 1)[0]
            self.assertLess(queue.index("High priority client"), queue.index("Low priority client"))
            self.assertNotIn("Employment role", queue)
            self.assertNotIn("Legacy unclassified", queue)
            self.assertNotIn("Closed client", queue)
            self.assertIn("Employment role", report)
            self.assertIn("No bids, cold messages", report)
            self.assertIn("unverified opportunities", report)

    def test_invalid_json_fails_closed_with_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leads_file = root / "data" / "leads.json"
            out_file = root / "data" / "opportunities" / "daily-company-review.md"
            leads_file.parent.mkdir(parents=True)
            leads_file.write_text("{not-json", encoding="utf-8")
            with patch.object(daily_company_review, "ROOT", root), \
                 patch.object(daily_company_review, "LEADS_FILE", leads_file), \
                 patch.object(daily_company_review, "OUT_FILE", out_file):
                self.assertEqual(daily_company_review.main(), 1)
            self.assertIn("ERROR: Could not read lead tracker", out_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
