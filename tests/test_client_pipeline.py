import json
import tempfile
import unittest
from pathlib import Path

from company.client_pipeline import build_client_pack, build_pack_from_lead


class ClientPipelineTests(unittest.TestCase):
    def test_generates_draft_without_sending_or_inventing_price(self):
        pack = build_client_pack(
            business_name="Example Cafe",
            website_url="https://example.com",
            service="business_website",
            observed_need="Needs a clear menu and contact path",
            evidence="Human-reviewed note",
        )
        self.assertEqual(pack["status"], "draft_requires_human_review")
        self.assertFalse(pack["sent"])
        self.assertIn("Price: not set", pack["proposal_markdown"])
        self.assertIn("not a claim", pack["outreach_draft"])
        self.assertIn("Proposed deliverables", pack["proposal_markdown"])

    def test_operator_price_is_labeled_as_unconfirmed_quote(self):
        pack = build_client_pack(
            business_name="Example Cafe",
            website_url="",
            service="landing_page",
            observed_need="Promote one event",
            price_quote="₹5,000",
        )
        self.assertIn("Indicative quote supplied by operator", pack["proposal_markdown"])
        self.assertIn("₹5,000", pack["proposal_markdown"])

    def test_builds_pack_from_explicit_client_project_lead(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "leads.json"
            store.write_text(json.dumps({"leads": [{
                "id": "TL-1", "business_name": "Example Cafe",
                "service": "business_website", "need": "Needs a menu page",
                "website_url": "https://example.com", "source_url": "https://example.org/project/1",
                "opportunity_type": "client_project", "client_fit": True, "paid_contract_verified": False,
                "evidence": "Public listing; not verified",
            }]}), encoding="utf-8")
            pack = build_pack_from_lead("TL-1", store_path=store)
            self.assertEqual(pack["business_name"], "Example Cafe")
            self.assertFalse(pack["sent"])
            self.assertIn("not sent or accepted", pack["proposal_markdown"])
            self.assertIn("Price: not set", pack["proposal_markdown"])

    def test_refuses_freelance_work_listing_as_client_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "leads.json"
            store.write_text(json.dumps({"leads": [{
                "id": "TL-2", "business_name": "Freelance role",
                "service": "business_website", "need": "Contract role",
                "opportunity_type": "freelance_work", "client_fit": False,
            }]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "explicitly classified as a client_project"):
                build_pack_from_lead("TL-2", store_path=store)

    def test_rejects_unknown_service(self):
        with self.assertRaises(ValueError):
            build_client_pack(business_name="Example", website_url="", service="magic",
                              observed_need="Need something")

    def test_requires_business_and_need(self):
        with self.assertRaises(ValueError):
            build_client_pack(business_name="", website_url="", service="website_audit",
                              observed_need="Need an audit")


if __name__ == "__main__":
    unittest.main()
