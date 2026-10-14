import unittest

from company.client_pipeline import build_client_pack


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
