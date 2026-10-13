import unittest
from company.opportunity_scout import score_listing, parse_feed

class OpportunityScoutTests(unittest.TestCase):
    def test_website_request_scores_high(self):
        s = score_listing("Need a business website redesign", "Paid freelance contract for small business")
        self.assertGreaterEqual(s["score"], 9)
        self.assertEqual(s["priority"], "high")
    def test_suspicious_listing_gets_risk_flag(self):
        s = score_listing("Website project", "Pay to apply for unpaid test")
        self.assertTrue(s["risk_flags"])
    def test_rss_parsing_returns_https_unverified_lead(self):
        xml = b"""<rss version="2.0"><channel><item><title>Website redesign freelance</title><link>https://jobs.example.org/123</link><description>Paid contract for website redesign</description></item></channel></rss>"""
        rows = parse_feed(xml, {"name":"test"})
        self.assertEqual(len(rows),1)
        self.assertFalse(rows[0]["paid_contract_verified"])
        self.assertEqual(rows[0]["status"],"new_lead")
    def test_non_https_listing_link_ignored(self):
        xml = b"""<rss version="2.0"><channel><item><title>Web design</title><link>http://bad.example/</link></item></channel></rss>"""
        self.assertEqual(parse_feed(xml, {"name":"test"}),[])

if __name__ == "__main__": unittest.main()
