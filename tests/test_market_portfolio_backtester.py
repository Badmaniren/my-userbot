import unittest
from unittest.mock import patch, mock_open
import json
import random
import uuid
import io
import os

from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester


class TestMarketPortfolioBacktester(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.filepath = f"{uuid.uuid4().hex}.json"

    def test_load_data_valid_json(self):
        random_price = round(random.uniform(10.0, 500.0), 2)
        random_timestamp = random.randint(1000000, 9999999)
        mock_data_dict = {
            self.symbol: [
                {"price": random_price, "timestamp": random_timestamp}
            ]
        }
        mock_content = json.dumps(mock_data_dict)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            backtester = MarketPortfolioBacktester(filepath=self.filepath)
            data = backtester.load_data(self.filepath)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol][0]["price"], random_price)
            self.assertEqual(data[self.symbol][0]["timestamp"], random_timestamp)

    def test_load_data_empty_file(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="   ")):
            backtester = MarketPortfolioBacktester(filepath=self.filepath)
            data = backtester.load_data(self.filepath)
            self.assertEqual(data, {})

    def test_load_data_exception(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=Exception("Disk read error")):
            backtester = MarketPortfolioBacktester(filepath=self.filepath)
            data = backtester.load_data(self.filepath)
            self.assertEqual(data, {})

    def test_run_backtest_with_shifts_list(self):
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        backtester = MarketPortfolioBacktester()
        backtester.data = {
            self.symbol: [
                {"price": 10.0, "timestamp": 100},
                {"price": 20.0, "timestamp": 200}
            ]
        }
        result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol]["status"], "completed")
        self.assertEqual(result[self.symbol]["shifts_tested"], len(shifts))
        for shift in shifts:
            res_key = f"{self.symbol}_shift_{shift}"
            self.assertIn(res_key, result)
            self.assertEqual(result[res_key]["shift"], shift)
            self.assertEqual(result[res_key]["data_points"], 2)

    def test_run_backtest_with_capital_and_strategy(self):
        initial_capital = round(random.uniform(1000.0, 10000.0), 2)
        buy_t = 50.0
        sell_t = 150.0
        strategy_params = {"buy_threshold": buy_t, "sell_threshold": sell_t}

        backtester = MarketPortfolioBacktester()
        backtester.data = {
            self.symbol: [
                {"price": 40.0, "timestamp": 1},
                {"price": 160.0, "timestamp": 2}
            ]
        }

        result = backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertEqual(result["total_trades"], 2)

    def test_run_backtest_empty_symbol_data(self):
        initial_capital = round(random.uniform(500.0, 5000.0), 2)
        backtester = MarketPortfolioBacktester()
        backtester.data = {}

        result = backtester.run_backtest(self.symbol, initial_capital)
        self.assertEqual(result["final_portfolio_value"], initial_capital)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["pnl_percentage"], 0.0)

    def test_calculate_maximum_drawdown(self):
        curve = [
            round(random.uniform(100.0, 110.0), 2),
            round(random.uniform(115.0, 130.0), 2),
            round(random.uniform(80.0, 95.0), 2),
            round(random.uniform(120.0, 140.0), 2)
        ]
        backtester = MarketPortfolioBacktester()
        max_dd = backtester.calculate_maximum_drawdown(curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)

    def test_calculate_maximum_drawdown_empty(self):
        backtester = MarketPortfolioBacktester()
        self.assertEqual(backtester.calculate_maximum_drawdown([]), 0.0)

    def test_simulate_historical_trades(self):
        allocation = round(random.uniform(10.0, 100.0), 2)
        p1 = round(random.uniform(10.0, 50.0), 2)
        p2 = round(random.uniform(51.0, 100.0), 2)
        t1 = random.randint(100, 200)
        t2 = random.randint(201, 300)

        backtester = MarketPortfolioBacktester()
        backtester.data = {
            self.symbol: [
                {"price": p1, "timestamp": t1},
                {"price": p2, "timestamp": t2}
            ]
        }

        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["action"], "BUY")
        self.assertEqual(trades[0]["price"], p1)
        self.assertEqual(trades[0]["allocation"], allocation)
        self.assertEqual(trades[0]["timestamp"], t1)

        self.assertEqual(trades[1]["action"], "SELL")
        self.assertEqual(trades[1]["price"], p2)

    def test_get_backtest_summary(self):
        backtester = MarketPortfolioBacktester()
        backtester.data = {
            self.symbol: [
                {"price": 10.0, "timestamp": 1},
                {"price": 11.0, "timestamp": 2},
                {"price": 12.0, "timestamp": 3}
            ]
        }
        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], 3)
        self.assertEqual(summary["status"], "ready")

    def test_market_backtester_alias(self):
        self.assertIs(MarketBacktester, MarketPortfolioBacktester)


if __name__ == "__main__":
    unittest.main()