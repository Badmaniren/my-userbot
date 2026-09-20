import unittest
import os
import uuid
import random
from skills.market_portfolio_analytics import PortfolioAnalytics, start_new

class TestPortfolioAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_market_storage_{self.unique_id}.json"
        self.symbol = f"SYM_{self.unique_id}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_url = f"https://example.com/market/{self.unique_id}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_portfolio_analytics_and_pipeline_integration(self):
        analytics = PortfolioAnalytics(storage_file=self.storage_file)
        
        initial_metrics = analytics.calculate_metrics(self.symbol)
        self.assertEqual(initial_metrics["symbol"], self.symbol)
        self.assertEqual(initial_metrics["return"], 0.0)
        self.assertEqual(initial_metrics["prices"], [])

        report = start_new(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.test_url,
            telegram_token=f"token_{self.unique_id}",
            chat_id=f"chat_{self.unique_id}"
        )

        self.assertIsNotNone(report)
        self.assertTrue(os.path.exists(self.storage_file))

        subsequent_metrics = analytics.calculate_metrics(self.symbol)
        self.assertEqual(subsequent_metrics["symbol"], self.symbol)
        self.assertIsInstance(subsequent_metrics["prices"], list)
        self.assertGreaterEqual(len(subsequent_metrics["prices"]), 1)
        self.assertIn(self.test_price, subsequent_metrics["prices"])

if __name__ == "__main__":
    unittest.main()