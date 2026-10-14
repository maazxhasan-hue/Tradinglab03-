import unittest
from company.opportunity_scout import score_listing, parse_feed, parse_remotive_api

class OpportunityScoutTests(unittest.TestCase):
    def test_website_request_scores_high(self):
        s = score_listing("Need a business website redesign", "Paid freelance contract project for a small business; looking for a freelancer")
        self.assertGreaterEqual(s["score"], 9)
        self.assertEqual(s["priority"], "high")
    def test_contract_job_vacancy_without_project_request_is_not_client_fit(self):
        s = score_listing(
            "Senior Shopify Developer",
            "We are hiring a contract-based developer to join our team. Full-time position with salary and benefits."
        )
        self.assertFalse(s["client_fit"])
        self.assertIn("no explicit service-project request", s["disqualifiers"])

    def test_suspicious_listing_gets_risk_flag(self):
        s = score_listing("Website project", "Pay to apply for unpaid test")
        self.assertTrue(s["risk_flags"])
    def test_rss_parsing_returns_https_unverified_lead(self):
        xml = b"""<rss version="2.0"><channel><item><title>Website redesign freelance</title><link>https://jobs.example.org/123</link><description>Paid contract for website redesign</description></item></channel></rss>"""
        rows = parse_feed(xml, {"name":"test"})
        self.assertEqual(len(rows),1)
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertEqual(rows[0]["status"],"new_lead")
    def test_remotive_json_api_parsing_returns_unverified_https_lead(self):
        payload = b'{"jobs":[{"id":123,"title":"Freelance website redesign","url":"https://remotive.com/remote-jobs/example","description":"Paid freelance contract project for a Shopify website redesign; looking for a freelancer","publication_date":"2026-10-14","job_type":"contract","candidate_required_location":"Worldwide","company_name":"Example Co"}]}'
        rows = parse_remotive_api(payload, {"name": "Remotive - All remote jobs"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://remotive.com/remote-jobs/example")
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertTrue(rows[0]["client_fit"])

    def test_remotive_json_api_ignores_non_https_links(self):
        payload = b'{"jobs":[{"title":"Website redesign","url":"http://bad.example/job","description":"Freelance contract"}]}'
        self.assertEqual(parse_remotive_api(payload, {"name": "Remotive"}), [])

    def test_non_https_listing_link_ignored(self):
        xml = b"""<rss version="2.0"><channel><item><title>Web design</title><link>http://bad.example/</link></item></channel></rss>"""
        self.assertEqual(parse_feed(xml, {"name":"test"}),[])

if __name__ == "__main__": unittest.main()
