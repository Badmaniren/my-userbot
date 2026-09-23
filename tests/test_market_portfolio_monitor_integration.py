import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, run_pipeline

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.mock-market-{uuid.uuid4().hex[:4]}.com/v1"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_portfolio_monitor_full_pipeline_integration(self):
        initial_price = round(random.uniform(10.0, 1500.0), 2)
        initial_data = {self.symbol: initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(pipeline_result)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, "r", encoding="utf-8") as f:
            stored_content = f.read()
            self.assertTrue(len(stored_content.strip()) > 0)
            parsed_data = json.loads(stored_content)
            self.assertIn(self.symbol, parsed_data)
            self.assertEqual(parsed_data[self.symbol], initial_price)

    def test_market_portfolio_monitor_start_new_entrypoint(self):
        start_price = round(random.uniform(50.0, 500.0), 2)
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({self.symbol: start_price}, f)

        execution_status = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(execution_status)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol], start_price)

if __name__ == "__main__":
    unittest.main()