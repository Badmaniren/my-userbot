import unittest
from unittest.mock import patch
import uuid
import random
import math
import tempfile
import os

from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics, start_new

class TestPortfolioPerformanceAnalytics(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_load_data_default_storage(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        random_data = [{"symbol": self.symbol, "price": random.uniform(10.0, 100.0)}]

        with patch.object(analytics.parser, 'load_data', return_value=random_data) as mock_load:
            data = analytics.load_data()
            mock_load.assert_called_once_with(self.storage_file)
            self.assertEqual(data, random_data)

    def test_load_data_custom_storage(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        custom_storage = f"{uuid.uuid4().hex}.json"
        random_data = [{"symbol": self.symbol, "price": random.uniform(50.0, 150.0)}]
        
        with patch.object(analytics.parser, 'load_data', return_value=random_data) as mock_load:
            data = analytics.load_data(custom_storage)
            mock_load.assert_called_once_with(custom_storage)
            self.assertEqual(data, random_data)

    def test_calculate_metrics_empty_data(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        with patch.object(analytics.parser, 'load_data', return_value=[]):
            metrics = analytics.calculate_metrics(self.symbol)
            expected = {
                "symbol": self.symbol,
                "return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0
            }
            self.assertEqual(metrics, expected)

    def test_calculate_metrics_single_price(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        single_price_data = [{"symbol": self.symbol, "price": random.uniform(10.0, 100.0)}]
        with patch.object(analytics.parser, 'load_data', return_value=single_price_data):
            metrics = analytics.calculate_metrics(self.symbol)
            expected = {
                "symbol": self.symbol,
                "return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0
            }
            self.assertEqual(metrics, expected)

    def test_calculate_metrics_multiple_prices(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        base_price = random.uniform(100.0, 200.0)
        prices = [base_price, base_price * 1.1, base_price * 1.05, base_price * 1.2]
        mock_data = [{"symbol": self.symbol, "price": p} for p in prices]

        with patch.object(analytics.parser, 'load_data', return_value=mock_data):
            metrics = analytics.calculate_metrics(self.symbol)
            
            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertIsInstance(metrics["return"], float)
            self.assertIsInstance(metrics["volatility"], float)
            self.assertIsInstance(metrics["sharpe_ratio"], float)

            expected_return = (prices[-1] - prices[0]) / prices[0]
            self.assertAlmostEqual(metrics["return"], expected_return)
            self.assertGreaterEqual(metrics["volatility"], 0.0)

    def test_calculate_metrics_zero_division_handling(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        prices = [0.0, 0.0, random.uniform(1.0, 10.0)]
        mock_data = [{"symbol": self.symbol, "price": p} for p in prices]

        with patch.object(analytics.parser, 'load_data', return_value=mock_data):
            metrics = analytics.calculate_metrics(self.symbol)
            self.assertEqual(metrics["symbol"], self.symbol)
            self.assertEqual(metrics["return"], 0.0)

    def test_evaluate_performance(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        random_price = random.uniform(10.0, 50.0)
        mock_data = [
            {"symbol": self.symbol, "price": random_price},
            {"symbol": self.symbol, "price": random_price * 2.0}
        ]
        with patch.object(analytics.parser, 'load_data', return_value=mock_data):
            res_eval = analytics.evaluate_performance(self.symbol)
            res_calc = analytics.calculate_metrics(self.symbol)
            self.assertEqual(res_eval, res_calc)

    def test_call_method_with_symbol(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        random_price = random.uniform(20.0, 80.0)
        mock_data = [
            {"symbol": self.symbol, "price": random_price},
            {"symbol": self.symbol, "price": random_price * 1.5}
        ]
        with patch.object(analytics.parser, 'load_data', return_value=mock_data):
            res_call = analytics(symbol=self.symbol)
            res_calc = analytics.calculate_metrics(self.symbol)
            self.assertEqual(res_call, res_calc)

    def test_call_method_without_arguments(self):
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        res = analytics()
        expected = {
            "return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0
        }
        self.assertEqual(res, expected)

    def test_start_new_function(self):
        url = f"https://{uuid.uuid4().hex}.com/market"
        mock_metrics = {
            "symbol": self.symbol,
            "return": random.uniform(0.1, 0.5),
            "volatility": random.uniform(0.01, 0.1),
            "sharpe_ratio": random.uniform(1.0, 3.0)
        }

        with patch('skills.market_portfolio_performance_analytics.MarketParser') as MockParserClass:
            mock_parser_instance = MockParserClass.return_value
            with patch('skills.market_portfolio_performance_analytics.PortfolioPerformanceAnalytics') as MockAnalyticsClass:
                mock_analytics_instance = MockAnalyticsClass.return_value
                mock_analytics_instance.calculate_metrics.return_value = mock_metrics

                result = start_new(self.storage_file, self.symbol, url)

                MockParserClass.assert_called_once_with(self.storage_file)
                mock_parser_instance.fetch_and_store.assert_called_once_with(self.symbol, url)
                MockAnalyticsClass.assert_called_once_with(self.storage_file)
                mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
                self.assertEqual(result, mock_metrics)

if __name__ == '__main__':
    unittest.main()