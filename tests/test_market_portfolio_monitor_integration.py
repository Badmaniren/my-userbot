import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, run_pipeline

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.mock-market-{uuid.uuid4()}.internal/v1"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_pipeline_integration_flow(self):
        initial_price = round(random.uniform(10.0, 1500.0), 2)
        initial_data = {self.symbol: initial_price}

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result, "Pipeline should execute successfully and return True.")
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must remain intact after pipeline execution.")

        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertIn(self.symbol, persisted_data)
        self.assertEqual(persisted_data[self.symbol], initial_price)

if __name__ == "__main__":
    unittest.main()