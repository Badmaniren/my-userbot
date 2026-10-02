import unittest
import os
import uuid
import random
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel, run_autonomous_sentinel

class TestAutonomousSentinelIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_sentinel_storage_{self.test_id}.json"
        self.symbol = f"TICKER_{self.test_id.upper()}"
        self.url = f"https://example.com/api/market/{self.test_id}"
        self.telegram_token = f"fake_token_{self.test_id}"
        self.chat_id = str(random.randint(100000, 999999))
        self.threshold = round(random.uniform(1.0, 10.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_autonomous_sentinel_pipeline_integration(self):
        sentinel = AutonomousSentinel(
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        self.assertEqual(sentinel.storage_file, self.storage_file)
        self.assertEqual(sentinel.threshold, self.threshold)

        result = run_autonomous_sentinel(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            threshold=self.threshold
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("forecast", result)
        self.assertIn(result["status"], ["triggered", "stable"])

        is_triggered_bool = bool(result)
        self.assertIsInstance(is_triggered_bool, bool)

if __name__ == "__main__":
    unittest.main()