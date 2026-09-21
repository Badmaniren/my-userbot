import unittest
from unittest.mock import patch
import uuid
import random
import math
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestMarketPortfolioPerformanceAnalytics(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.analytics = PortfolioPerformanceAnalytics(self.storage_file)

    def test_load_data_delegation(self):
        mock_data = [{"symbol": self.symbol, "price": random.uniform(10.0, 100.0)}]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data) as mock_load:
            res = self.analytics.load_data(self.storage_file)
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(res, mock_data)

    def test_calculate_metrics_empty_data(self):
        with patch("skills.market_parser.MarketParser.load_data", return_value=[]):
            res = self.analytics.calculate_metrics(self.symbol)
            self.assertEqual(res["symbol"], self.symbol)
            self.assertEqual(res["return"], 0.0)
            self.assertEqual(res["volatility"], 0.0)
            self.assertEqual(res["sharpe_ratio"], 0.0)

    def test_calculate_metrics_single_price(self):
        single_item = [{"symbol": self.symbol, "price": random.uniform(50.0, 150.0)}]
        with patch("skills.market_parser.MarketParser.load_data", return_value=single_item):
            res = self.analytics.calculate_metrics(self.symbol)
            self.assertEqual(res["return"], 0.0)
            self.assertEqual(res["volatility"], 0.0)
            self.assertEqual(res["sharpe_ratio"], 0.0)

    def test_calculate_metrics_multiple_prices(self):
        p1 = 100.0
        p2 = 105.0
        p3 = 121.0
        mock_data = [
            {"symbol": self.symbol, "price": p1},
            {"symbol": self.symbol, "price": p2},
            {"symbol": self.symbol, "price": p3}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            res = self.analytics.calculate_metrics(self.symbol)
            expected_return = (p3 - p1) / p1
            self.assertAlmostEqual(res["return"], expected_return)
            self.assertGreater(res["volatility"], 0.0)
            self.assertGreater(res["sharpe_ratio"], 0.0)

    def test_calculate_metrics_zero_previous_price(self):
        mock_data = [
            {"symbol": self.symbol, "price": 0.0},
            {"symbol": self.symbol, "price": 50.0},
            {"symbol": self.symbol, "price": 100.0}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            res = self.analytics.calculate_metrics(self.symbol)
            self.assertIn("return", res)
            self.assertIn("volatility", res)
            self.assertIn("sharpe_ratio", res)

    def test_evaluate_performance(self):
        mock_data = [
            {"symbol": self.symbol, "price": 10.0},
            {"symbol": self.symbol, "price": 20.0}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            res = self.analytics.evaluate_performance(self.symbol)
            self.assertEqual(res["symbol"], self.symbol)
            self.assertAlmostEqual(res["return"], 1.0)

    def test_call_with_symbol(self):
        mock_data = [
            {"symbol": self.symbol, "price": 15.0},
            {"symbol": self.symbol, "price": 30.0}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            res = self.analytics(symbol=self.symbol)
            self.assertEqual(res["symbol"], self.symbol)

    def test_call_without_symbol(self):
        res = self.analytics()
        self.assertEqual(res["return"], 0.0)
        self.assertEqual(res["volatility"], 0.0)
        self.assertEqual(res["sharpe_ratio"], 0.0)

    def test_start_new_function_empty(self):
        url = f"https://example.com/{uuid.uuid4().hex}"
        with patch("skills.market_parser.MarketParser.load_data", return_value=[]):
            res = start_new(self.storage_file, self.symbol, url)
            self.assertEqual(res["symbol"], self.symbol)
            self.assertEqual(res["return"], 0.0)

    def test_start_new_function_populated(self):
        url = f"https://example.com/{uuid.uuid4().hex}"
        mock_data = [
            {"symbol": self.symbol, "price": 200.0},
            {"symbol": self.symbol, "price": 250.0}
        ]
        with patch("skills.market_parser.MarketParser.load_data", return_value=mock_data):
            res = start_new(self.storage_file, self.symbol, url)
            self.assertEqual(res["symbol"], self.symbol)
            self.assertAlmostEqual(res["return"], 0.25)

if __name__ == "__main__":
    unittest.main()