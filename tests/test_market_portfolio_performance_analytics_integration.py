import unittest
import os
import uuid
import random
from skills.market_parser import MarketParser
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"test_portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_integration_performance_analytics_pipeline(self):
        parser = MarketParser(self.storage_file)
        
        base_price = round(random.uniform(100.0, 500.0), 2)
        prices = [base_price]
        for _ in range(5):
            change = random.uniform(-10.0, 15.0)
            base_price = round(max(10.0, base_price + change), 2)
            prices.append(base_price)

        for p in prices:
            parser.fetch_and_store(self.symbol, p)

        analytics = PortfolioPerformanceAnalytics(self.storage_file)

        loaded_data = analytics.load_data()
        self.assertIsInstance(loaded_data, list)
        self.assertGreaterEqual(len(loaded_data), len(prices))

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

        evaluated = analytics.evaluate_performance(self.symbol)
        self.assertEqual(evaluated, metrics)

        callable_res = analytics(symbol=self.symbol)
        self.assertEqual(callable_res, metrics)

        empty_callable_res = analytics()
        self.assertEqual(empty_callable_res["return"], 0.0)

    def test_integration_start_new_function(self):
        new_storage = os.path.join(self.test_dir, f"start_new_{uuid.uuid4().hex}.json")
        try:
            random_price = round(random.uniform(50.0, 1000.0), 2)
            result_metrics = start_new(new_storage, self.symbol, random_price)

            self.assertIsInstance(result_metrics, dict)
            self.assertEqual(result_metrics["symbol"], self.symbol)
            self.assertEqual(result_metrics["return"], 0.0)
            self.assertEqual(result_metrics["volatility"], 0.0)

            self.assertTrue(os.path.exists(new_storage))
        finally:
            if os.path.exists(new_storage):
                os.remove(new_storage)

if __name__ == "__main__":
    unittest.main()