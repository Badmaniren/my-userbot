import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_analytics_pipeline(self):
        price_1 = round(random.uniform(10.0, 50.0), 2)
        price_2 = round(price_1 * random.uniform(1.01, 1.15), 2)
        price_3 = round(price_2 * random.uniform(0.90, 0.99), 2)

        import json
        raw_data = [
            {"symbol": self.symbol, "price": price_1},
            {"symbol": self.symbol, "price": price_2},
            {"symbol": self.symbol, "price": price_3}
        ]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f)

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)

        self.assertIn("symbol", metrics)
        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertIn("return", metrics)
        self.assertIn("volatility", metrics)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIsInstance(metrics["return"], float)
        self.assertIsInstance(metrics["volatility"], float)
        self.assertIsInstance(metrics["sharpe_ratio"], float)

        evaluated = analytics.evaluate_performance(self.symbol)
        self.assertEqual(evaluated["symbol"], self.symbol)

        callable_result = analytics(symbol=self.symbol)
        self.assertEqual(callable_result["symbol"], self.symbol)

        empty_callable = analytics()
        self.assertIn("return", empty_callable)
        self.assertEqual(empty_callable["return"], 0.0)

        url_dummy = f"http://example.com/{uuid.uuid4().hex}"
        start_new_result = start_new(self.storage_file, self.symbol, url_dummy)
        self.assertEqual(start_new_result["symbol"], self.symbol)
        self.assertIn("return", start_new_result)

if __name__ == "__main__":
    unittest.main()