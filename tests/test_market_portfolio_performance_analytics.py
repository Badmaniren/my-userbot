import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_performance_analytics import (
    PortfolioPerformanceAnalytics,
    start_new,
)


class TestPortfolioPerformanceAnalytics(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.analytics = PortfolioPerformanceAnalytics(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"

    def test_load_data_none(self):
        with patch.object(self.analytics.parser, "load_data", return_value=None):
            res = self.analytics.load_data(self.storage_file)
            self.assertEqual(res, [])

    def test_load_data_dict(self):
        rand_dict = {"symbol": self.symbol, "price": random.uniform(10.0, 100.0)}
        with patch.object(self.analytics.parser, "load_data", return_value=rand_dict):
            res = self.analytics.load_data(self.storage_file)
            self.assertEqual(res, [rand_dict])

    def test_load_data_iterable_conversion(self):
        rand_tuple = (
            {"symbol": self.symbol, "price": random.uniform(10.0, 100.0)},
        )
        with patch.object(self.analytics.parser, "load_data", return_value=rand_tuple):
            res = self.analytics.load_data(self.storage_file)
            self.assertEqual(res, list(rand_tuple))

    def test_load_data_invalid_type_fallback(self):
        with patch.object(self.analytics.parser, "load_data", return_value=12345):
            res = self.analytics.load_data(self.storage_file)
            self.assertEqual(res, [])

    def test_calculate_metrics_insufficient_data(self):
        rand_price = random.uniform(50.0, 500.0)
        mock_data = [{"symbol": self.symbol, "price": rand_price}]
        with patch.object(self.analytics, "load_data", return_value=mock_data):
            metrics = self.analytics.calculate_metrics(self.symbol)
            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)
            self.assertEqual(metrics["sharpe_ratio"], 0.0)

    def test_calculate_metrics_valid_prices(self):
        p1 = random.uniform(10.0, 50.0)
        p2 = p1 * random.uniform(1.1, 1.5)
        p3 = p2 * random.uniform(0.8, 0.95)
        mock_data = [
            {"symbol": self.symbol, "price": p1},
            {"symbol": self.symbol, "price": p2},
            {"symbol": self.symbol, "price": p3},
        ]
        with patch.object(self.analytics, "load_data", return_value=mock_data):
            metrics = self.analytics.calculate_metrics(self.symbol)
            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertIsInstance(metrics["return"], float)
            self.assertIsInstance(metrics["volatility"], float)
            self.assertIsInstance(metrics["sharpe_ratio"], float)
            self.assertNotEqual(metrics["return"], 0.0)

    def test_calculate_metrics_zero_previous_price(self):
        mock_data = [
            {"symbol": self.symbol, "price": 0.0},
            {"symbol": self.symbol, "price": random.uniform(10.0, 50.0)},
        ]
        with patch.object(self.analytics, "load_data", return_value=mock_data):
            metrics = self.analytics.calculate_metrics(self.symbol)
            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertIsInstance(metrics["volatility"], float)

    def test_calculate_metrics_bool_price_ignored(self):
        mock_data = [
            {"symbol": self.symbol, "price": True},
            {"symbol": self.symbol, "price": 100.0},
            {"symbol": self.symbol, "price": 200.0},
        ]
        with patch.object(self.analytics, "load_data", return_value=mock_data):
            metrics = self.analytics.calculate_metrics(self.symbol)
            self.assertEqual(metrics["symbol"], self.symbol)

    def test_evaluate_performance(self):
        rand_price = random.uniform(1.0, 10.0)
        mock_data = [{"symbol": self.symbol, "price": rand_price}]
        with patch.object(self.analytics, "load_data", return_value=mock_data):
            res = self.analytics.evaluate_performance(self.symbol)
            self.assertEqual(res["symbol"], self.symbol)

    def test_call_method_with_symbol(self):
        rand_price = random.uniform(1.0, 10.0)
        mock_data = [{"symbol": self.symbol, "price": rand_price}]
        with patch.object(self.analytics, "load_data", return_value=mock_data):
            res = self.analytics(symbol=self.symbol)
            self.assertEqual(res["symbol"], self.symbol)

    def test_call_method_without_symbol(self):
        res = self.analytics(symbol=None)
        self.assertEqual(res["return"], 0.0)
        self.assertEqual(res["volatility"], 0.0)
        self.assertEqual(res["sharpe_ratio"], 0.0)

    def test_start_new_function(self):
        rand_url = f"https://{uuid.uuid4().hex}.org/api"
        rand_price = random.uniform(5.0, 50.0)
        mock_data = [{"symbol": self.symbol, "price": rand_price}]
        with patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics.load_data", return_value=mock_data):
            res = start_new(self.storage_file, self.symbol, rand_url)
            self.assertEqual(res["symbol"], self.symbol)


if __name__ == "__main__":
    unittest.main()