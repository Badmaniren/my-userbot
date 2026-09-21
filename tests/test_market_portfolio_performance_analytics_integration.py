import unittest
import os
import tempfile
import uuid
from skills.market_parser import MarketParser
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

        self.parser = MarketParser(self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_analytics_flow(self):
        price_1 = float(uuid.uuid4().int % 100 + 50)
        price_2 = price_1 * 1.1
        price_3 = price_2 * 0.95
        
        self.parser.fetch_and_store(self.symbol, price_1)
        self.parser.fetch_and_store(self.symbol, price_2)
        self.parser.fetch_and_store(self.symbol, price_3)

        analytics = PortfolioPerformanceAnalytics(self.storage_file)

        loaded_data = analytics.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, list)
        self.assertGreaterEqual(len(loaded_data), 3)

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

        callable_result = analytics(symbol=self.symbol)
        self.assertEqual(callable_result, metrics)

        empty_callable_result = analytics()
        self.assertEqual(empty_callable_result["return"], 0.0)

        start_new_result = start_new(self.storage_file, self.symbol, "http://example.com")
        self.assertEqual(start_new_result["symbol"], self.symbol)
        self.assertIn("return", start_new_result)
        self.assertIn("volatility", start_new_result)
        self.assertIn("sharpe_ratio", start_new_result)

        chart = analytics.generate_ascii_chart(self.symbol)
        self.assertIsInstance(chart, str)
        self.assertIn("#", chart)

        report = analytics.build_performance_report(self.symbol)
        self.assertIsInstance(report, str)
        self.assertIn(self.symbol, report)
        self.assertIn("Performance Report", report)

if __name__ == "__main__":
    unittest.main()