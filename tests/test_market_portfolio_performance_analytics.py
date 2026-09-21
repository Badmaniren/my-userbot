import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io
from skills.market_portfolio_performance_analytics import (
    PortfolioPerformanceAnalytics,
    start_new
)

class TestPortfolioPerformanceAnalytics(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def test_calculate_metrics_insufficient_data(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = [
                {"symbol": rand_symbol, "price": round(random.uniform(10.0, 100.0), 2)}
            ]

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(rand_symbol)

            self.assertEqual(metrics["symbol"], rand_symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)
            self.assertEqual(metrics["sharpe_ratio"], 0.0)

    def test_calculate_metrics_valid_data(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        prices = [100.0, 105.0, 102.0, 110.0]
        mock_data = [{"symbol": rand_symbol, "price": p} for p in prices]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(rand_symbol)

            expected_return = (110.0 - 100.0) / 100.0
            self.assertEqual(metrics["symbol"], rand_symbol)
            self.assertAlmostEqual(metrics["return"], expected_return, places=4)
            self.assertGreater(metrics["volatility"], 0.0)
            self.assertIsInstance(metrics["sharpe_ratio"], float)

    def test_evaluate_performance(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        mock_data = [
            {"symbol": rand_symbol, "price": 50.0},
            {"symbol": rand_symbol, "price": 75.0}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            res = analytics.evaluate_performance(rand_symbol)

            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["return"], 0.5, places=4)

    def test_call_method_with_symbol(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        mock_data = [
            {"symbol": rand_symbol, "price": 200.0},
            {"symbol": rand_symbol, "price": 100.0}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            res = analytics(symbol=rand_symbol)

            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["return"], -0.5, places=4)

    def test_call_method_without_symbol(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        res = analytics()

        self.assertEqual(res["return"], 0.0)
        self.assertEqual(res["volatility"], 0.0)
        self.assertEqual(res["sharpe_ratio"], 0.0)

    def test_start_new_function(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_url = f"https://example.com/{uuid.uuid4().hex}"
        mock_data = [
            {"symbol": rand_symbol, "price": 10.0},
            {"symbol": rand_symbol, "price": 20.0}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            res = start_new(self.storage_file, rand_symbol, rand_url)

            self.assertEqual(res["symbol"], rand_symbol)
            self.assertAlmostEqual(res["return"], 1.0, places=4)

    def test_load_data_custom_file(self):
        custom_file = f"custom_{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            expected_output = [{"symbol": rand_symbol, "price": 123.45}]
            instance.load_data.return_value = expected_output

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            data = analytics.load_data(custom_file)

            instance.load_data.assert_called_once_with(custom_file)
            self.assertEqual(data, expected_output)

    def test_zero_division_price_handling(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        mock_data = [
            {"symbol": rand_symbol, "price": 0.0},
            {"symbol": rand_symbol, "price": 50.0}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(rand_symbol)

            self.assertEqual(metrics["symbol"], rand_symbol)
            self.assertEqual(metrics["return"], 0.0)

    def test_generate_ascii_chart_and_build_report(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        mock_data = [
            {"symbol": rand_symbol, "price": 50.0},
            {"symbol": rand_symbol, "price": 75.0}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as MockParser:
            instance = MockParser.return_value
            instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            chart = analytics.generate_ascii_chart(rand_symbol)
            self.assertIn("50.00", chart)
            self.assertIn("#", chart)

            report = analytics.build_performance_report(rand_symbol)
            self.assertIn(rand_symbol, report)
            self.assertIn("Performance Report", report)
            self.assertIn("Price Dynamics", report)

if __name__ == "__main__":
    unittest.main()