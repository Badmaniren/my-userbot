import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io
from skills.market_portfolio_performance_analytics import (
    PortfolioPerformanceAnalytics,
    start_new,
)


class TestPortfolioPerformanceAnalytics(unittest.TestCase):
    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def test_load_data_none(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        with patch.object(analytics.parser, "load_data", return_value=None):
            res = analytics.load_data()
            self.assertEqual(res, [])

    def test_load_data_dict(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        mock_item = {"symbol": self.random_symbol, "price": random.uniform(10.0, 100.0)}
        with patch.object(analytics.parser, "load_data", return_value=mock_item):
            res = analytics.load_data()
            self.assertEqual(res, [mock_item])

    def test_load_data_iterable_conversion(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        mock_tuple = (
            {"symbol": self.random_symbol, "price": 42.0},
        )
        with patch.object(analytics.parser, "load_data", return_value=mock_tuple):
            res = analytics.load_data()
            self.assertEqual(res, [{"symbol": self.random_symbol, "price": 42.0}])

    def test_load_data_exception_handling(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        class BadIterable:
            def __iter__(self):
                raise TypeError("fail")
        with patch.object(analytics.parser, "load_data", return_value=BadIterable()):
            res = analytics.load_data()
            self.assertEqual(res, [])

    def test_calculate_metrics_insufficient_data(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        single_item = {"symbol": self.random_symbol, "price": 100.0}
        with patch.object(analytics, "load_data", return_value=[single_item]):
            metrics = analytics.calculate_metrics(self.random_symbol)
            self.assertEqual(metrics["symbol"], self.random_symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)
            self.assertEqual(metrics["sharpe_ratio"], 0.0)

    def test_calculate_metrics_zero_division_prevention(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        data = [
            {"symbol": self.random_symbol, "price": 0.0},
            {"symbol": self.random_symbol, "price": 50.0},
            {"symbol": self.random_symbol, "price": 100.0},
        ]
        with patch.object(analytics, "load_data", return_value=data):
            metrics = analytics.calculate_metrics(self.random_symbol)
            self.assertIsInstance(metrics, dict)
            self.assertIn("return", metrics)
            self.assertIn("volatility", metrics)
            self.assertIn("sharpe_ratio", metrics)

    def test_calculate_metrics_valid_series(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        p1 = random.uniform(10.0, 50.0)
        p2 = p1 * 1.08
        p3 = p2 * 1.02
        data = [
            {"symbol": self.random_symbol, "price": p1},
            {"symbol": self.random_symbol, "price": p2},
            {"symbol": self.random_symbol, "price": p3},
            {"symbol": f"OTHER_{uuid.uuid4().hex[:4]}", "price": 999.0},
            {"symbol": self.random_symbol, "price": "invalid"},
            {"symbol": self.random_symbol, "price": True},
        ]
        with patch.object(analytics, "load_data", return_value=data):
            metrics = analytics.calculate_metrics(self.random_symbol)
            self.assertEqual(metrics["symbol"], self.random_symbol)
            self.assertAlmostEqual(metrics["return"], (p3 - p1) / p1, places=5)
            self.assertGreater(metrics["volatility"], 0.0)

    def test_evaluate_performance(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        with patch.object(analytics, "calculate_metrics") as mock_calc:
            dummy_res = {"symbol": self.random_symbol, "return": 0.5, "volatility": 0.1, "sharpe_ratio": 5.0}
            mock_calc.return_value = dummy_res
            res = analytics.evaluate_performance(self.random_symbol)
            mock_calc.assert_called_once_with(self.random_symbol)
            self.assertEqual(res, dummy_res)

    def test_call_method_with_symbol(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        with patch.object(analytics, "calculate_metrics") as mock_calc:
            dummy_res = {"symbol": self.random_symbol, "return": 0.1, "volatility": 0.05, "sharpe_ratio": 2.0}
            mock_calc.return_value = dummy_res
            res = analytics(symbol=self.random_symbol)
            mock_calc.assert_called_once_with(self.random_symbol)
            self.assertEqual(res, dummy_res)

    def test_call_method_without_symbol(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        res = analytics(url=f"http://{uuid.uuid4().hex}.com")
        self.assertEqual(res, {"return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0})

    def test_start_new_function(self):
        random_file = f"{uuid.uuid4().hex}.json"
        random_sym = f"TICK_{uuid.uuid4().hex[:4]}"
        random_url = f"https://{uuid.uuid4().hex}.org"
        with patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics") as MockClass:
            instance = MockClass.return_value
            expected_dict = {"symbol": random_sym, "return": 0.2, "volatility": 0.02, "sharpe_ratio": 10.0}
            instance.calculate_metrics.return_value = expected_dict

            res = start_new(random_file, random_sym, random_url)
            MockClass.assert_called_once_with(random_file)
            instance.calculate_metrics.assert_called_once_with(random_sym)
            self.assertEqual(res, expected_dict)

    def test_calculate_metrics_symbol_keyed_dict_list(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        data = {
            self.random_symbol: [
                {"price": 100.0},
                {"value": 110.0},
                {"close": 125.0},
            ]
        }
        with patch.object(analytics, "load_data", return_value=[data]):
            metrics = analytics.calculate_metrics(self.random_symbol)
            self.assertEqual(metrics["symbol"], self.random_symbol)
            self.assertAlmostEqual(metrics["return"], 0.25, places=5)
            self.assertGreater(metrics["volatility"], 0.0)

    def test_calculate_metrics_symbol_keyed_numeric_list(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        data = {
            self.random_symbol: [50.0, 55.0, 60.5]
        }
        with patch.object(analytics, "load_data", return_value=[data]):
            metrics = analytics.calculate_metrics(self.random_symbol)
            self.assertEqual(metrics["symbol"], self.random_symbol)
            self.assertAlmostEqual(metrics["return"], 0.21, places=5)

    def test_calculate_metrics_symbol_keyed_single_dict(self):
        analytics = PortfolioPerformanceAnalytics(self.random_storage)
        data = {
            self.random_symbol: {"price": 100.0}
        }
        with patch.object(analytics, "load_data", return_value=[data]):
            metrics = analytics.calculate_metrics(self.random_symbol)
            self.assertEqual(metrics["symbol"], self.random_symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)