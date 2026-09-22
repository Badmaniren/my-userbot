import os
import json
import unittest
import uuid
import random
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway, start_new, run_pipeline
from skills.db_storage import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioAPIGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"http://example.com/market/{self.unique_id}"
        self.telegram_token = f"token_{random.randint(10000, 99999)}"
        self.chat_id = str(random.randint(100000, 999999))
        
        initial_data = {
            self.symbol: {
                "price": round(random.uniform(10.0, 1000.0), 2),
                "history": [round(random.uniform(10.0, 1000.0), 2) for _ in range(5)]
            }
        }
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_portfolio_api_gateway_integration(self):
        gateway = MarketPortfolioAPIGateway(self.storage_file)
        self.assertIsInstance(gateway.valuation, PortfolioValuation)
        self.assertIsInstance(gateway.parser, MarketParser)

        summary = gateway.export_portfolio_summary(self.url)
        self.assertIsNotNone(summary)

        pipeline_result = run_pipeline(
            self.symbol, 
            self.url, 
            self.telegram_token, 
            self.chat_id, 
            self.storage_file
        )
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result.get("symbol"), self.symbol)

        start_result = start_new(
            self.symbol, 
            self.url, 
            self.telegram_token, 
            self.chat_id, 
            self.storage_file
        )
        self.assertIsInstance(start_result, dict)
        self.assertIn("status", start_result)

    def test_gateway_error_handling_integration(self):
        invalid_storage = f"invalid_{self.unique_id}.json"
        start_result = start_new(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            invalid_storage
        )
        self.assertIsInstance(start_result, dict)
        self.assertEqual(start_result.get("status"), "error")
        self.assertIn("message", start_result)

if __name__ == "__main__":
    unittest.main()