import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalytics(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_init_and_load_data_list(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        random_price = round(random.uniform(10.0, 1000.0), 2)
        mock_data = [{"symbol": self.symbol, "price": random_price}]
        mock_parser.load_data.return_value = mock_data

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        loaded = analytics.load_data(self.storage_file)

        self.assertEqual(loaded, mock_data)
        mock_parser.load_data.assert_called_once_with(self.storage_file)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_load_data_dict_format(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        random_price = round(random.uniform(50.0, 500.0), 2)
        raw_dict = {
            self.symbol: {
                "price": random_price,
                "timestamp": uuid.uuid4().hex
            }
        }
        mock_parser.load_data.return_value = raw_dict

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        loaded = analytics.load_data()

        self.assertIsInstance(loaded, list)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["symbol"], self.symbol)
        self.assertEqual(loaded[0]["price"], random_price)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_load_data_dict_simple_value(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        random_price = round(random.uniform(1.0, 100.0), 2)
        raw_dict = {
            self.symbol: random_price
        }
        mock_parser.load_data.return_value = raw_dict

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        loaded = analytics.load_data()

        self.assertIsInstance(loaded, list)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["symbol"], self.symbol)
        self.assertEqual(loaded[0]["price"], random_price)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_load_data_unexpected_type(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        mock_parser.load_data.return_value = random.choice([12345, "invalid_string", None])

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        loaded = analytics.load_data()

        self.assertEqual(loaded, [])

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_calculate_metrics_insufficient_data(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        random_price = round(random.uniform(10.0, 100.0), 2)
        mock_parser.load_data.return_value = [{"symbol": self.symbol, "price": random_price}]

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)

        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertEqual(metrics["return"], 0.0)
        self.assertEqual(metrics["volatility"], 0.0)
        self.assertEqual(metrics["sharpe_ratio"], 0.0)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_calculate_metrics_success(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        base_price = 100.0
        prices = [base_price, base_price * 1.1, base_price * 1.05, base_price * 1.25]
        mock_data = [{"symbol": self.symbol, "price": p} for p in prices]
        mock_parser.load_data.return_value = mock_data

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)

        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertAlmostEqual(metrics["return"], (prices[-1] - prices[0]) / prices[0])
        self.assertGreater(metrics["volatility"], 0.0)
        self.assertIsInstance(metrics["sharpe_ratio"], float)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_calculate_metrics_nested_history(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        p1 = round(random.uniform(10.0, 50.0), 2)
        p2 = round(random.uniform(51.0, 100.0), 2)
        mock_data = [
            {
                "symbol": self.symbol,
                "history": [
                    {"price": p1},
                    {"price": p2}
                ]
            }
        ]
        mock_parser.load_data.return_value = mock_data

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)

        self.assertEqual(metrics["symbol"], self.symbol)
        expected_return = (p2 - p1) / p1
        self.assertAlmostEqual(metrics["return"], expected_return)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_evaluate_performance(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        p1 = 200.0
        p2 = 250.0
        mock_parser.load_data.return_value = [{"symbol": self.symbol, "price": p1}, {"symbol": self.symbol, "price": p2}]

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.evaluate_performance(self.symbol)

        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertAlmostEqual(metrics["return"], 0.25)

    @patch("skills.market_portfolio_performance_analytics.MarketParser")
    def test_call_method_with_symbol(self, mock_market_parser_cls):
        mock_parser = mock_market_parser_cls.return_value
        p1 = 50.0
        p2 = 75.0
        mock_parser.load_data.return_value = [{"symbol": self.symbol, "price": p1}, {"symbol": self.symbol, "price": p2}]

        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics(symbol=self.symbol)

        self.assertEqual(metrics["symbol"], self.symbol)
        self.assertAlmostEqual(metrics["return"], 0.5)

    def test_call_method_without_symbol(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics()

        self.assertEqual(metrics["return"], 0.0)
        self.assertEqual(metrics["volatility"], 0.0)
        self.assertEqual(metrics["sharpe_ratio"], 0.0)

    @patch("skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics")
    def test_start_new_function(self, mock_analytics_cls):
        mock_instance = mock_analytics_cls.return_value
        random_return = round(random.uniform(0.01, 0.99), 4)
        mock_instance.calculate_metrics.return_value = {
            "symbol": self.symbol,
            "return": random_return,
            "volatility": 0.1,
            "sharpe_ratio": 1.5
        }

        url = f"https://example.com/{uuid.uuid4().hex}"
        result = start_new(self.storage_file, self.symbol, url)

        mock_analytics_cls.assert_called_once_with(self.storage_file)
        mock_instance.calculate_metrics.assert_called_once_with(self.symbol)
        self.assertEqual(result["return"], random_return)