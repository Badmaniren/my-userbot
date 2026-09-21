import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_parser import MarketParser

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.parser = MarketParser(self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_performance_analytics_integration_with_real_parser(self):
        base_price = round(random.uniform(10.0, 100.0), 2)
        price_steps = [base_price]
        
        for _ in range(5):
            delta = random.uniform(-5.0, 5.0)
            next_price = max(1.0, round(price_steps[-1] + delta, 2))
            price_steps.append(next_price)

        for p in price_steps:
            self.parser.fetch_and_store(self.symbol, p)

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
        self.assertEqual(evaluated, metrics)

        called_metrics = analytics(symbol=self.symbol)
        self.assertEqual(called_metrics, metrics)

        empty_symbol = f"EMPTY_{uuid.uuid4().hex[:6].upper()}"
        empty_metrics = analytics.calculate_metrics(empty_symbol)
        self.assertEqual(empty_metrics["return"], 0.0)
        self.assertEqual(empty_metrics["volatility"], 0.0)
        self.assertEqual(empty_metrics["sharpe_ratio"], 0.0)

if __name__ == "__main__":
    unittest.main()