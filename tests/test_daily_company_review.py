import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company import daily_company_review


class DailyCompanyReviewTests(unittest.TestCase):
    def test_generates_prioritized_read_only_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leads_file = root / "data" / "leads.json"
            out_file = root / "data" / "opportunities" / "daily-company-review.md"
            leads_file.parent.mkdir(parents=True)
            leads_file.write_text(json.dumps({"leads": [
                {"business_name": "Low priority", "opportunity_priority": "low",
                 "opportunity_score": 10, "status": "new",
                 "source_url": "https://example.com/low",
                 "next_action": "Verify listing"},
                {"business_name": "High priority", "opportunity_priority": "high",
                 "opportunity_score": 80, "status": "new",
                 "source_url": "https://example.com/high",
                 "next_action": "Review fit"},
                {"business_name": "Malformed score", "opportunity_priority": "medium",
                 "opportunity_score": "not-a-number", "status": "new"},
            ]}), encoding="utf-8")
            with patch.object(daily_company_review, "ROOT", root), \
                 patch.object(daily_company_review, "LEADS_FILE", leads_file), \
                 patch.object(daily_company_review, "OUT_FILE", out_file):
                self.assertEqual(daily_company_review.main(), 0)
            report = out_file.read_text(encoding="utf-8")
            self.assertIn("Total tracked records: 3", report)
            self.assertLess(report.index("High priority"), report.index("Low priority"))
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
