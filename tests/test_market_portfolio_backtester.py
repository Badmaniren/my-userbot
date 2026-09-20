import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.market_portfolio_backtester import PortfolioBacktester


class TestPortfolioBacktester(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)

    def test_backtester_initialization(self):
        backtester = PortfolioBacktester(self.storage_file)
        self.assertEqual(backtester.storage_file, self.storage_file)

    def test_load_historical_data_success(self):
        mock_data = {
            self.symbol: [
                {"timestamp": uuid.uuid4().hex, "price": round(random.uniform(10.0, 500.0), 2)},
                {"timestamp": uuid.uuid4().hex, "price": round(random.uniform(10.0, 500.0), 2)}
            ]
        }
        json_content = json.dumps(mock_data).encode('utf-8')

        with patch('builtins.open', unittest.mock.mock_open(read_data=json_content)):
            backtester = PortfolioBacktester(self.storage_file)
            data = backtester.load_historical_data(self.symbol)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["price"], mock_data[self.symbol][0]["price"])

    def test_load_historical_data_file_not_found(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            backtester = PortfolioBacktester(self.storage_file)
            data = backtester.load_historical_data(self.symbol)
            self.assertEqual(data, [])

    def test_run_backtest_logic(self):
        price_1 = round(random.uniform(50.0, 100.0), 2)
        price_2 = round(random.uniform(101.0, 200.0), 2)

        mock_data = {
            self.symbol: [
                {"timestamp": "2023-01-01", "price": price_1},
                {"timestamp": "2023-01-02", "price": price_2}
            ]
        }
        json_content = json.dumps(mock_data).encode('utf-8')

        with patch('builtins.open', unittest.mock.mock_open(read_data=json_content)):
            backtester = PortfolioBacktester(self.storage_file)
            result = backtester.run_backtest(self.symbol, self.initial_capital)

            self.assertIn("final_value", result)
            self.assertIn("total_return", result)
            expected_return = ((price_2 - price_1) / price_1) * 100
            self.assertAlmostEqual(result["total_return"], expected_return, places=2)

    def test_run_backtest_empty_data(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            backtester = PortfolioBacktester(self.storage_file)
            result = backtester.run_backtest(self.symbol, self.initial_capital)

            self.assertEqual(result["final_value"], self.initial_capital)
            self.assertEqual(result["total_return"], 0.0)

    def test_calculate_max_drawdown(self):
        prices = [100.0, 120.0, 80.0, 90.0, 60.0, 110.0]
        mock_data = {
            self.symbol: [{"timestamp": str(i), "price": p} for i, p in enumerate(prices)]
        }
        json_content = json.dumps(mock_data).encode('utf-8')

        with patch('builtins.open', unittest.mock.mock_open(read_data=json_content)):
            backtester = PortfolioBacktester(self.storage_file)
            drawdown = backtester.calculate_max_drawdown(self.symbol)

            # Peak is 120, trough is 60 after peak. Drawdown is (120-60)/120 = 50%
            self.assertAlmostEqual(drawdown, 50.0, places=2)


if __name__ == '__main__':
    unittest.main()