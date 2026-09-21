import unittest
import os
import tempfile
import uuid
import random
from skills.market_parser import MarketParser
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

        self.parser = MarketParser(self.storage_file)

        self.prices = [
            round(random.uniform(10.0, 50.0), 2),
            round(random.uniform(50.1, 100.0), 2),
            round(random.uniform(100.1, 150.0), 2),
            round(random.uniform(150.1, 200.0), 2)
        ]

        for price in self.prices:
            self.parser.fetch_and_store(self.symbol, price)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_calculate_metrics(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)

        self.assertIsInstance(metrics, dict)
        self.assertIn("symbol", metrics)
        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertIn("return", metrics)
        self.assertIn("volatility", metrics)
        self.assertIn("sharpe_ratio", metrics)

        self.assertIsInstance(metrics["return"], float)
        self.assertIsInstance(metrics["volatility"], float)
        self.assertIsInstance(metrics["sharpe_ratio"], float)
        
        expected_return = (self.prices[-1] - self.prices[0]) / self.prices[0]
        self.assertAlmostEqual(metrics["return"], expected_return, places=4)

    def test_integration_evaluate_performance(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.evaluate_performance(self.symbol)

        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertGreaterEqual(metrics["volatility"], 0.0)

    def test_integration_start_new_function(self):
        url_stub = f"http://example.com/{uuid.uuid4().hex}"
        metrics = start_new(self.storage_file, self.symbol, url_stub)

        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertIn("return", metrics)
        self.assertIn("volatility", metrics)
        self.assertIn("sharpe_ratio", metrics)

    def test_integration_callable_interface(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics(symbol=self.symbol)

        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["symbol"], self.symbol)

        empty_metrics = analytics()
        self.assertIsInstance(empty_metrics, dict)
        self.assertEqual(empty_metrics["return"], 0.0)
        self.assertEqual(empty_metrics["volatility"], 0.0)
        self.assertEqual(empty_metrics["sharpe_ratio"], 0.0)

if __name__ == "__main__":
    unittest.main()