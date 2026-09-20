import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway, start_new, run_pipeline

class TestMarketPortfolioAPIGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.random_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.random_id}.json"
        self.symbol = f"TICK_{self.random_id}"
        self.url = f"http://example.com/market/{self.random_id}"
        self.telegram_token = f"fake_token_{self.random_id}"
        self.chat_id = str(random.randint(100000, 999999))
        
        initial_data = {
            self.symbol: [
                {"price": round(random.uniform(10.0, 1000.0), 2), "timestamp": "2023-10-01T00:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_gateway_and_pipeline_integration(self):
        gateway = MarketPortfolioAPIGateway(self.storage_file)
        self.assertEqual(gateway.storage_file, self.storage_file)

        summary = gateway.export_portfolio_summary(self.url)
        self.assertIsNotNone(summary)

        result = run_pipeline(
            self.symbol, 
            self.url, 
            self.telegram_token, 
            self.chat_id, 
            self.storage_file
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("price", result)
        self.assertIn("timestamp", result)

        start_result = start_new(
            self.symbol, 
            self.url, 
            self.telegram_token, 
            self.chat_id, 
            self.storage_file
        )
        self.assertIsInstance(start_result, dict)
        self.assertEqual(start_result.get("status"), "success")
        self.assertEqual(start_result.get("symbol"), self.symbol)

    def test_pipeline_empty_storage_flow(self):
        empty_storage = f"empty_storage_{self.random_id}.json"
        with open(empty_storage, "w", encoding="utf-8") as f:
            json.dump({}, f)
        
        try:
            result = start_new(
                self.symbol, 
                self.url, 
                self.telegram_token, 
                self.chat_id, 
                empty_storage
            )
            self.assertIn(result.get("status"), ["completed_empty", "success", "error"])
        finally:
            if os.path.exists(empty_storage):
                os.remove(empty_storage)

if __name__ == "__main__":
    unittest.main()