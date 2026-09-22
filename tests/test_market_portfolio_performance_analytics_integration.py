import unittest
import os
import uuid
import random
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_parser import MarketParser


class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"

        self.parser = MarketParser(self.storage_file)
        self.analytics = PortfolioPerformanceAnalytics(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_metrics_calculation(self):
        base_price = round(random.uniform(100.0, 500.0), 2)
        price_step_1 = round(base_price * random.uniform(1.01, 1.05), 2)
        price_step_2 = round(price_step_1 * random.uniform(0.95, 0.99), 2)
        price_step_3 = round(price_step_2 * random.uniform(1.02, 1.08), 2)

        prices = [base_price, price_step_1, price_step_2, price_step_3]

        for p in prices:
            self.parser.fetch_and_store(self.symbol, p)

        self.assertTrue(os.path.exists(self.storage_file))

        metrics = self.analytics.calculate_metrics(self.symbol)

        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics.get("symbol"), self.symbol)
        self.assertIn("return", metrics)
        self.assertIn("volatility", metrics)
        self.assertIn("sharpe_ratio", metrics)

        expected_return = (prices[-1] - prices[0]) / prices[0]
        self.assertAlmostEqual(metrics["return"], float(expected_return), places=5)
        self.assertGreaterEqual(metrics["volatility"], 0.0)
        self.assertIsInstance(metrics["sharpe_ratio"], float)

    def test_integration_empty_or_single_data(self):
        metrics = self.analytics.calculate_metrics(self.symbol)

        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics.get("symbol"), self.symbol)
        self.assertEqual(metrics.get("return"), 0.0)
        self.assertEqual(metrics.get("volatility"), 0.0)
        self.assertEqual(metrics.get("sharpe_ratio"), 0.0)

        single_price = round(random.uniform(50.0, 150.0), 2)
        self.parser.fetch_and_store(self.symbol, single_price)

        single_metrics = self.analytics.evaluate_performance(self.symbol)
        self.assertEqual(single_metrics.get("return"), 0.0)
        self.assertEqual(single_metrics.get("volatility"), 0.0)
        self.assertEqual(single_metrics.get("sharpe_ratio"), 0.0)


if __name__ == "__main__":
    unittest.main()