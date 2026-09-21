import unittest
import os
import uuid
import random
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_analytics_pipeline(self):
        from skills.market_parser import MarketParser
        parser = MarketParser(self.storage_file)
        
        base_price = round(random.uniform(10.0, 100.0), 2)
        prices = [base_price]
        for _ in range(5):
            change = random.uniform(-5.0, 5.0)
            base_price = round(max(1.0, base_price + change), 2)
            prices.append(base_price)

        for p in prices:
            parser.fetch_and_store(self.symbol, p)

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        loaded_data = analytics.load_data()
        self.assertIsInstance(loaded_data, list)
        self.assertGreaterEqual(len(loaded_data), len(prices))

        metrics = analytics.calculate_metrics(self.symbol)
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertIn("return", metrics)
        self.assertIn("volatility", metrics)
        self.assertIn("sharpe_ratio", metrics)

        eval_perf = analytics.evaluate_performance(self.symbol)
        self.assertEqual(eval_perf, metrics)

        call_result = analytics(symbol=self.symbol)
        self.assertEqual(call_result["symbol"], self.symbol)

        empty_call = analytics()
        self.assertEqual(empty_call["return"], 0.0)

        functional_result = start_new(self.storage_file, self.symbol, "http://localhost/dummy")
        self.assertEqual(functional_result["symbol"], self.symbol)
        self.assertIn("volatility", functional_result)

if __name__ == "__main__":
    unittest.main()