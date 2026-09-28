import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_collector_agent import start_new, run_pipeline

class TestMarketPortfolioCollectorAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.example.com/v1/market/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = f"-100{random.randint(100000000, 999999999)}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_execution_and_storage_side_effects(self):
        random_price = round(random.uniform(10.0, 5000.0), 2)
        
        self.assertFalse(os.path.exists(self.storage_file), "Storage file should not exist prior to test execution.")

        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result, "The pipeline should execute successfully and return True.")
        self.assertTrue(os.path.exists(self.storage_file), "The pipeline must create the storage file as a side effect.")

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIsInstance(data, list, "Stored data must be a JSON list.")
        self.assertGreaterEqual(len(data), 1, "Storage must contain at least one recorded entry.")
        
        recorded_entry = data[0]
        self.assertEqual(recorded_entry.get("symbol"), self.symbol, "The recorded symbol must match the input symbol.")
        self.assertIn("price", recorded_entry, "Recorded entry must contain a price field.")
        self.assertIn("timestamp", recorded_entry, "Recorded entry must contain a timestamp field.")

    def test_run_pipeline_idempotency_with_existing_data(self):
        initial_data = [{
            "symbol": "PREV_SYMBOL",
            "price": 999.9,
            "timestamp": "2023-01-01T00:00:00"
        }]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result)

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(len(data), 1, "Existing storage should not be appended with a new parser entry if file already existed.")
        self.assertEqual(data[0]["symbol"], "PREV_SYMBOL", "Original storage content must remain intact.")

if __name__ == '__main__':
    unittest.main()