import unittest
from company.site_audit import analyze_html, validate_public_https_url

class SiteAuditTests(unittest.TestCase):
    def test_detects_missing_mobile_and_seo_signals(self):
        result = analyze_html("https://example.org", "<html><body><p>Hello</p><img src='x.png'></body></html>")
        needs = {f["need"] for f in result["findings"]}
        self.assertIn("missing page title", needs)
        self.assertIn("missing mobile viewport", needs)
        self.assertIn("images missing alternative text", needs)
    def test_recognizes_good_basic_metadata(self):
        result = analyze_html("https://example.org", "<html><head><title>Example</title><meta name='description' content='A business'><meta name='viewport' content='width=device-width'></head><body><h1>Welcome</h1><a href='/contact'>Contact</a></body></html>")
        self.assertEqual(result["page_title"], "Example")
        self.assertTrue(result["meta_description_present"])
        self.assertTrue(result["mobile_viewport_present"])
    def test_rejects_http_url(self):
        with self.assertRaises(ValueError):
            validate_public_https_url("http://example.org")
    def test_rejects_localhost(self):
        with self.assertRaises(ValueError):
            validate_public_https_url("https://localhost")

if __name__ == "__main__": unittest.main()
