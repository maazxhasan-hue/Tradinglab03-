import tempfile
import unittest
from pathlib import Path
from company.service_pricing import PricingStore, PricingValidationError, MAX_SERVICE_PRICE

class PricingStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "prices.sqlite3"
        self.store = PricingStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_are_capped_and_persisted(self):
        rows = self.store.list_services()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(1 <= row["price"] <= 499 for row in rows))
        self.store.update_service("landing-page", 250)
        reopened = PricingStore(self.path)
        self.assertEqual(next(r["price"] for r in reopened.list_services() if r["service_id"] == "landing-page"), 250)

    def test_rejects_prices_at_or_above_500_and_invalid_values(self):
        for value in (0, 500, 999, -1, "abc", 1.5, True, None):
            with self.subTest(value=value):
                with self.assertRaises(PricingValidationError):
                    self.store.update_service("landing-page", value)

    def test_unknown_service_rejected(self):
        with self.assertRaises(KeyError):
            self.store.update_service("not-a-service", 100)

if __name__ == "__main__":
    unittest.main()
