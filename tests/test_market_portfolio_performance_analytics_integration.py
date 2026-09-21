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
        self.storage_file = os.path.join(self.test_dir.name, f"test_market_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
        self.parser = MarketParser(self.storage_file)
        
        self.base_price = round(random.uniform(10.0, 100.0), 2)
        self.prices = [self.base_price]
        
        current_price = self.base_price
        for _ in range(5):
            change = random.uniform(-0.05, 0.05)
            current_price = round(current_price * (1 + change), 2)
            self.prices.append(current_price)
            
        for p in self.prices:
            self.parser.fetch_and_store(self.symbol, p)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_calculate_metrics_and_load_data(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        
        loaded_data = analytics.load_data(self.storage_file)
        self.assertTrue(isinstance(loaded_data, list))
        self.assertGreaterEqual(len(loaded_data), len(self.prices))
        
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
        self.assertEqual(evaluated["symbol"], metrics["symbol"])
        self.assertEqual(evaluated["return"], metrics["return"])
        
        callable_metrics = analytics(symbol=self.symbol)
        self.assertEqual(callable_metrics["symbol"], self.symbol)
        
        empty_callable = analytics()
        self.assertEqual(empty_callable["return"], 0.0)

if __name__ == "__main__":
    unittest.main()