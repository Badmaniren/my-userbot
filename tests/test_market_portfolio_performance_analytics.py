import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new


class TestPortfolioPerformanceAnalytics(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/market"

    def test_load_data_delegates_to_parser(self):
        custom_storage = f"{uuid.uuid4().hex}.json"
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            expected_data = [{"symbol": self.symbol, "price": float(random.randint(10, 100))}]
            mock_parser_instance.load_data.return_value = expected_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            result = analytics.load_data(custom_storage)

            mock_parser_instance.load_data.assert_called_once_with(custom_storage)
            self.assertEqual(result, expected_data)

    def test_calculate_metrics_no_data(self):
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = []

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(self.symbol)

            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)
            self.assertEqual(metrics["sharpe_ratio"], 0.0)

    def test_calculate_metrics_single_price_point(self):
        single_price = float(random.randint(50, 500))
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = [
                {"symbol": self.symbol, "price": single_price}
            ]

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(self.symbol)

            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)
            self.assertEqual(metrics["sharpe_ratio"], 0.0)

    def test_calculate_metrics_multiple_price_points(self):
        p1 = float(random.randint(100, 200))
        p2 = p1 * 1.1
        p3 = p2 * 0.95
        mock_data = [
            {"symbol": self.symbol, "price": p1},
            {"symbol": f"OTHER_{uuid.uuid4().hex[:4]}", "price": 999.0},
            {"symbol": self.symbol, "price": p2},
            {"symbol": self.symbol, "price": p3}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(self.symbol)

            expected_return = (p3 - p1) / p1
            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertAlmostEqual(metrics["return"], float(expected_return), places=5)
            self.assertGreater(metrics["volatility"], 0.0)

    def test_calculate_metrics_zero_previous_price(self):
        mock_data = [
            {"symbol": self.symbol, "price": 0.0},
            {"symbol": self.symbol, "price": float(random.randint(10, 50))}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = mock_data

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.calculate_metrics(self.symbol)

            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertEqual(metrics["return"], 0.0)

    def test_evaluate_performance(self):
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = []

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics.evaluate_performance(self.symbol)

            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertEqual(metrics["return"], 0.0)

    def test_call_method_with_symbol(self):
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = []

            analytics = PortfolioPerformanceAnalytics(self.storage_file)
            metrics = analytics(symbol=self.symbol)

            self.assertEqual(metrics["symbol"], self.symbol)

    def test_call_method_without_symbol(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics(url=self.url)

        self.assertEqual(metrics["return"], 0.0)
        self.assertEqual(metrics["volatility"], 0.0)
        self.assertEqual(metrics["sharpe_ratio"], 0.0)
        self.assertNotIn("symbol", metrics)

    def test_start_new_function(self):
        p1 = float(random.randint(10, 50))
        p2 = float(random.randint(60, 100))
        mock_data = [
            {"symbol": self.symbol, "price": p1},
            {"symbol": self.symbol, "price": p2}
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = mock_data

            result = start_new(self.storage_file, self.symbol, self.url)

            expected_return = (p2 - p1) / p1
            self.assertEqual(result["symbol"], self.symbol)
            self.assertAlmostEqual(result["return"], float(expected_return), places=5)