import math
import random
import string
import unittest
from unittest.mock import MagicMock, patch

from skills.market_portfolio_performance_analytics import (
    PortfolioPerformanceAnalytics,
    start_new,
)


def _rnd_str(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _rnd_symbol():
    return "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))


class TestPortfolioPerformanceAnalytics(unittest.TestCase):

    def test_init(self):
        rnd_file = f"/tmp/{_rnd_str()}.json"
        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            analytics = PortfolioPerformanceAnalytics(rnd_file)
            self.assertEqual(analytics.storage_file, rnd_file)
            mock_parser_cls.assert_called_once_with(rnd_file)

    def test_load_data_delegation(self):
        default_file = f"/tmp/{_rnd_str()}.json"
        custom_file = f"/tmp/{_rnd_str()}.json"
        rnd_dataset = [{_rnd_str(): random.random()}]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser_instance = MagicMock()
            mock_parser_cls.return_value = mock_parser_instance
            mock_parser_instance.load_data.return_value = rnd_dataset

            analytics = PortfolioPerformanceAnalytics(default_file)

            res_default = analytics.load_data()
            mock_parser_instance.load_data.assert_called_with(default_file)
            self.assertEqual(res_default, rnd_dataset)

            res_custom = analytics.load_data(custom_file)
            mock_parser_instance.load_data.assert_called_with(custom_file)
            self.assertEqual(res_custom, rnd_dataset)

    def test_calculate_metrics_empty_data(self):
        storage_file = f"{_rnd_str()}.db"
        symbol = _rnd_symbol()

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = []
            mock_parser_cls.return_value = mock_parser

            analytics = PortfolioPerformanceAnalytics(storage_file)
            metrics = analytics.calculate_metrics(symbol)

            expected = {
                "symbol": symbol,
                "return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
            }
            self.assertEqual(metrics, expected)

    def test_calculate_metrics_single_price_record(self):
        storage_file = f"{_rnd_str()}.dat"
        symbol = _rnd_symbol()
        price = random.uniform(10.0, 1000.0)

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = [{"symbol": symbol, "price": price}]
            mock_parser_cls.return_value = mock_parser

            analytics = PortfolioPerformanceAnalytics(storage_file)
            metrics = analytics.calculate_metrics(symbol)

            self.assertEqual(metrics["symbol"], symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertEqual(metrics["volatility"], 0.0)
            self.assertEqual(metrics["sharpe_ratio"], 0.0)

    def test_calculate_metrics_filters_other_symbols_and_malformed_items(self):
        storage_file = f"{_rnd_str()}.json"
        target_symbol = _rnd_symbol()
        other_symbol = target_symbol + "_OTHER"
        prices = [random.uniform(50.0, 100.0) for _ in range(3)]

        noisy_data = [
            f"corrupted_raw_string_{_rnd_str()}",
            None,
            42,
            {"symbol": other_symbol, "price": random.uniform(10.0, 20.0)},
            {"symbol": target_symbol},
            {"price": random.uniform(10.0, 20.0)},
            {"symbol": target_symbol, "price": prices[0]},
            {"symbol": other_symbol, "price": random.uniform(10.0, 20.0)},
            {"symbol": target_symbol, "price": prices[1]},
            [],
            {"symbol": target_symbol, "price": prices[2]},
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = noisy_data
            mock_parser_cls.return_value = mock_parser

            analytics = PortfolioPerformanceAnalytics(storage_file)
            metrics = analytics.calculate_metrics(target_symbol)

            r1 = (prices[1] - prices[0]) / prices[0]
            r2 = (prices[2] - prices[1]) / prices[1]
            mean_ret = (r1 + r2) / 2.0
            variance = ((r1 - mean_ret) ** 2 + (r2 - mean_ret) ** 2) / 2.0
            expected_vol = math.sqrt(variance)
            expected_return = (prices[2] - prices[0]) / prices[0]
            expected_sharpe = mean_ret / expected_vol if expected_vol > 0 else 0.0

            self.assertEqual(metrics["symbol"], target_symbol)
            self.assertAlmostEqual(metrics["return"], expected_return, places=7)
            self.assertAlmostEqual(metrics["volatility"], expected_vol, places=7)
            self.assertAlmostEqual(metrics["sharpe_ratio"], expected_sharpe, places=7)

    def test_calculate_metrics_mathematical_precision(self):
        storage_file = f"{_rnd_str()}.db"
        symbol = _rnd_symbol()
        prices = [random.uniform(10.0, 500.0) for _ in range(random.randint(4, 8))]

        mock_data = [{"symbol": symbol, "price": p} for p in prices]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = mock_data
            mock_parser_cls.return_value = mock_parser

            analytics = PortfolioPerformanceAnalytics(storage_file)
            metrics = analytics.calculate_metrics(symbol)

            returns = []
            for i in range(1, len(prices)):
                returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
            expected_return = (prices[-1] - prices[0]) / prices[0]
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            expected_vol = math.sqrt(variance)
            expected_sharpe = (mean_ret / expected_vol) if expected_vol > 0 else 0.0

            self.assertEqual(metrics["symbol"], symbol)
            self.assertAlmostEqual(metrics["return"], expected_return, places=7)
            self.assertAlmostEqual(metrics["volatility"], expected_vol, places=7)
            self.assertAlmostEqual(metrics["sharpe_ratio"], expected_sharpe, places=7)

    def test_calculate_metrics_zero_price_handling(self):
        storage_file = f"{_rnd_str()}.json"
        symbol = _rnd_symbol()
        mock_data = [
            {"symbol": symbol, "price": 0.0},
            {"symbol": symbol, "price": random.uniform(10.0, 50.0)},
            {"symbol": symbol, "price": 0.0},
        ]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = mock_data
            mock_parser_cls.return_value = mock_parser

            analytics = PortfolioPerformanceAnalytics(storage_file)
            metrics = analytics.calculate_metrics(symbol)

            self.assertEqual(metrics["symbol"], symbol)
            self.assertEqual(metrics["return"], 0.0)
            self.assertIsInstance(metrics["volatility"], float)
            self.assertIsInstance(metrics["sharpe_ratio"], float)

    def test_calculate_metrics_zero_volatility_sharpe(self):
        storage_file = f"{_rnd_str()}.csv"
        symbol = _rnd_symbol()
        fixed_price = random.uniform(10.0, 100.0)
        mock_data = [{"symbol": symbol, "price": fixed_price} for _ in range(4)]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = mock_data
            mock_parser_cls.return_value = mock_parser

            analytics = PortfolioPerformanceAnalytics(storage_file)
            metrics = analytics.calculate_metrics(symbol)

            self.assertEqual(metrics["symbol"], symbol)
            self.assertAlmostEqual(metrics["return"], 0.0, places=7)
            self.assertAlmostEqual(metrics["volatility"], 0.0, places=7)
            self.assertAlmostEqual(metrics["sharpe_ratio"], 0.0, places=7)

    def test_evaluate_performance_delegates_to_calculate_metrics(self):
        storage_file = f"{_rnd_str()}.db"
        symbol = _rnd_symbol()
        expected_metrics = {
            "symbol": symbol,
            "return": random.random(),
            "volatility": random.random(),
            "sharpe_ratio": random.random(),
        }

        with patch("skills.market_portfolio_performance_analytics.MarketParser"):
            analytics = PortfolioPerformanceAnalytics(storage_file)
            with patch.object(analytics, "calculate_metrics", return_value=expected_metrics) as mock_calc:
                result = analytics.evaluate_performance(symbol)
                mock_calc.assert_called_once_with(symbol)
                self.assertEqual(result, expected_metrics)

    def test_call_magic_method_with_symbol(self):
        storage_file = f"{_rnd_str()}.db"
        symbol = _rnd_symbol()
        url = f"https://example.com/{_rnd_str()}"
        expected_metrics = {
            "symbol": symbol,
            "return": random.random(),
            "volatility": random.random(),
            "sharpe_ratio": random.random(),
        }

        with patch("skills.market_portfolio_performance_analytics.MarketParser"):
            analytics = PortfolioPerformanceAnalytics(storage_file)
            with patch.object(analytics, "calculate_metrics", return_value=expected_metrics) as mock_calc:
                result = analytics(symbol=symbol, url=url)
                mock_calc.assert_called_once_with(symbol)
                self.assertEqual(result, expected_metrics)

    def test_call_magic_method_without_symbol(self):
        storage_file = f"{_rnd_str()}.db"
        url = f"https://example.com/{_rnd_str()}"

        with patch("skills.market_portfolio_performance_analytics.MarketParser"):
            analytics = PortfolioPerformanceAnalytics(storage_file)
            result = analytics(url=url)
            self.assertEqual(
                result,
                {"return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0},
            )

    def test_start_new_function_computation(self):
        storage_file = f"/tmp/{_rnd_str()}.json"
        symbol = _rnd_symbol()
        url = f"https://example.com/api/{_rnd_str()}"
        prices = [random.uniform(20.0, 150.0) for _ in range(4)]
        mock_data = [{"symbol": symbol, "price": p} for p in prices]

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = mock_data
            mock_parser_cls.return_value = mock_parser

            result = start_new(storage_file, symbol, url)
            mock_parser_cls.assert_called_once_with(storage_file)
            mock_parser.load_data.assert_called_once_with(storage_file)

            returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
            expected_return = (prices[-1] - prices[0]) / prices[0]
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            expected_vol = math.sqrt(variance)
            expected_sharpe = mean_ret / expected_vol if expected_vol > 0 else 0.0

            self.assertEqual(result["symbol"], symbol)
            self.assertAlmostEqual(result["return"], expected_return, places=7)
            self.assertAlmostEqual(result["volatility"], expected_vol, places=7)
            self.assertAlmostEqual(result["sharpe_ratio"], expected_sharpe, places=7)

    def test_start_new_function_empty_and_single_entry(self):
        storage_file = f"/tmp/{_rnd_str()}.json"
        symbol = _rnd_symbol()
        url = f"https://example.com/{_rnd_str()}"

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = []
            mock_parser_cls.return_value = mock_parser

            res_empty = start_new(storage_file, symbol, url)
            self.assertEqual(
                res_empty,
                {"symbol": symbol, "return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0},
            )

        with patch("skills.market_portfolio_performance_analytics.MarketParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = [{"symbol": symbol, "price": random.uniform(10.0, 50.0)}]
            mock_parser_cls.return_value = mock_parser

            res_single = start_new(storage_file, symbol, url)
            self.assertEqual(
                res_single,
                {"symbol": symbol, "return": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0},
            )


if __name__ == "__main__":
    unittest.main()