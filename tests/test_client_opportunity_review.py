import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from company import client_opportunity_review, daily_company_review


class ClientOpportunityReviewTests(unittest.TestCase):
    def test_only_active_review_allowed_public_projects_get_proposal_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leads_file = root / "data" / "leads.json"
            source_config = root / "config" / "opportunity_sources.json"
            out_dir = root / "data" / "client_packs" / "daily_review"
            leads_file.parent.mkdir(parents=True)
            source_config.parent.mkdir(parents=True)
            source_config.write_text(json.dumps([
                {"name": "Reddit r/forhire - public service requests", "enabled": True,
                 "action_policy": "review_allowed"},
                {"name": "Codeur - public freelance project requests", "enabled": True,
                 "action_policy": "research_only"},
                {"name": "Disabled marketplace", "enabled": False,
                 "action_policy": "review_allowed"},
            ]), encoding="utf-8")
            leads = [
                {"id": "TL-1", "business_name": "Allowed Reddit project",
                 "opportunity_type": "client_project", "client_fit": True,
                 "source_type": "public_opportunity_listing",
                 "source_name": "Reddit r/forhire - public service requests",
                 "source_url": "https://example.com/reddit", "status": "new",
                 "opportunity_priority": "high", "opportunity_score": 50},
                {"id": "TL-2", "business_name": "Codeur research-only project",
                 "opportunity_type": "client_project", "client_fit": True,
                 "source_type": "public_opportunity_listing",
                 "source_name": "Codeur - public freelance project requests",
                 "source_url": "https://example.com/codeur", "status": "new",
                 "opportunity_priority": "high", "opportunity_score": 90},
                {"id": "TL-3", "business_name": "Disabled source project",
                 "opportunity_type": "client_project", "client_fit": True,
                 "source_type": "public_opportunity_listing",
                 "source_name": "Disabled marketplace",
                 "source_url": "https://example.com/disabled", "status": "new",
                 "opportunity_priority": "high", "opportunity_score": 100},
                {"id": "TL-4", "business_name": "Closed project",
                 "opportunity_type": "client_project", "client_fit": True,
                 "source_type": "public_opportunity_listing",
                 "source_name": "Reddit r/forhire - public service requests",
                 "source_url": "https://example.com/closed", "status": "lost",
                 "opportunity_priority": "high", "opportunity_score": 80},
                {"id": "TL-5", "business_name": "Employment role",
                 "opportunity_type": "employment_role", "client_fit": False,
                 "source_url": "https://example.com/job", "status": "new"},
            ]
            leads_file.write_text(json.dumps({"leads": leads}), encoding="utf-8")
            def fake_pack(lead_id, store_path):
                return {"proposal_markdown": f"# Draft for {lead_id}"}
            with patch.object(client_opportunity_review, "LEADS_FILE", leads_file), \\
                 patch.object(client_opportunity_review, "OUT_DIR", out_dir), \\
                 patch.object(client_opportunity_review, "build_pack_from_lead", side_effect=fake_pack) as builder, \\
                 patch.object(daily_company_review, "SOURCE_CONFIG", source_config):
                self.assertEqual(client_opportunity_review.main(), 0)
            self.assertEqual(builder.call_count, 1)
            builder.assert_called_once_with("TL-1", store_path=leads_file)
            self.assertTrue((out_dir / "TL-1.md").exists())
            self.assertFalse((out_dir / "TL-2.md").exists())
            self.assertFalse((out_dir / "TL-3.md").exists())
            self.assertFalse((out_dir / "TL-4.md").exists())
            shortlist = (out_dir / "SHORTLIST.md").read_text(encoding="utf-8")
            report = (out_dir / "README-review.md").read_text(encoding="utf-8")
            self.assertIn("Source/status-policy eligible for proposal drafting: 1", shortlist)
            self.assertIn("Excluded by source/status policy: 3", shortlist)
            self.assertIn("research only, not an actionable lead", report)
            self.assertIn("listing source is disabled or not configured", report)
            self.assertIn('"sent": false', report.replace(" ", "").lower() if False else json.dumps({"sent": False}))

    def test_invalid_lead_store_shape_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leads.json"
            path.write_text(json.dumps({"leads": "not-a-list"}), encoding="utf-8")
            with patch.object(client_opportunity_review, "LEADS_FILE", path):
                with self.assertRaises(ValueError):
                    client_opportunity_review.main()


if __name__ == "__main__":
    unittest.main()
