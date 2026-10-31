import unittest
from unittest.mock import patch
from company.business_intelligence import BusinessObservation, analyze_business, can_contact, analyze_public_website

class BusinessIntelligenceTests(unittest.TestCase):
    def test_observed_need_maps_to_services(self):
        o=BusinessObservation("Example Co","https://example.com",("outdated website","no booking"),("home page review",),True)
        result=analyze_business(o)
        self.assertIn("website redesign",result.services)
        self.assertIn("booking/contact workflow",result.services)
        self.assertEqual(result.confidence,"medium")
    def test_no_observations_does_not_invent_specific_issue(self):
        result=analyze_business(BusinessObservation("Example","https://example.com",(),()))
        self.assertEqual(result.services,())
        self.assertEqual(result.confidence,"low")
    @patch("company.site_audit.audit_public_homepage")
    def test_website_analysis_uses_observed_findings(self, audit):
        audit.return_value = {"findings":[{"service":"SEO metadata setup","evidence":"No page title"}]}
        result = analyze_public_website("Example","https://example.com")
        self.assertIn("SEO metadata setup",result.services)
        self.assertIn("No page title",result.rationale)

    def test_contact_requires_all_approvals(self):
        o=BusinessObservation("Example","https://example.com",("no website",),())
        result=analyze_business(o)
        self.assertFalse(can_contact(result,consent_or_lawful_basis_checked=True,channel_approved=True,human_approved_message=False))

if __name__ == "__main__": unittest.main()
