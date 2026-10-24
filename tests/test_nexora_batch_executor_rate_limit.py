import unittest
from unittest.mock import patch

from company import nexora_batch_executor as batch


class ProviderCooldownTests(unittest.TestCase):
    def setUp(self):
        batch._provider_cooldown_until = 0.0

    def test_rate_limit_cooldown_sets_future_deadline(self):
        with patch.object(batch.time, "monotonic", return_value=100.0):
            batch._cool_down_provider(30)
        self.assertEqual(batch._provider_cooldown_until, 130.0)

    def test_cooldown_never_shortens_existing_deadline(self):
        batch._provider_cooldown_until = 200.0
        with patch.object(batch.time, "monotonic", return_value=100.0):
            batch._cool_down_provider(30)
        self.assertEqual(batch._provider_cooldown_until, 200.0)

    def test_cooldown_enforces_minimum_delay(self):
        with patch.object(batch.time, "monotonic", return_value=100.0):
            batch._cool_down_provider(0)
        self.assertEqual(batch._provider_cooldown_until, 101.0)

    def test_wait_does_not_sleep_when_cooldown_expired(self):
        batch._provider_cooldown_until = 99.0
        with patch.object(batch.time, "monotonic", return_value=100.0), patch.object(batch.time, "sleep") as sleep:
            batch._wait_for_provider_slot()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
