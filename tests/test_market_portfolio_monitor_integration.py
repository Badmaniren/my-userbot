import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.example.com/v1/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_portfolio_monitor_pipeline_integration(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result, "Pipeline should return True on success")
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created during pipeline execution")

        with open(self.storage_file, "r", encoding="utf-8") as f:
            stored_data = json.load(f)

        self.assertIsInstance(stored_data, dict, "Stored data must be a dictionary")
        self.assertIn(self.symbol, stored_data, f"Symbol {self.symbol} must be present in storage")
        self.assertEqual(stored_data[self.symbol], 0.0, "Initial price must be recorded as 0.0")

if __name__ == "__main__":
    unittest.main()