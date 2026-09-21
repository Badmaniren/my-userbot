import unittest
from unittest.mock import patch
import json
import os
import io
import uuid
import random
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester

class TestMarketPortfolioBacktester(unittest.TestCase):

    def setUp(self):
        self.random_filepath = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.random_capital = round(random.uniform(1000.0, 50000.0), 2)
        self.prices = [round(random.uniform(10.0, 500.0), 2) for _ in range(random.randint(5, 15))]
        
        self.mock_data = {
            self.symbol: [{"price": p, "timestamp": random.randint(1600000000, 1700000000)} for p in self.prices]
        }

    def tearDown(self):
        if os.path.exists(self.random_filepath):
            try:
                os.remove(self.random_filepath)
            except OSError:
                pass

    def test_load_data_valid_json(self):
        json_content = json.dumps(self.mock_data)
        with patch('builtins.open', return_value=io.StringIO(json_content)), \
             patch('os.path.exists', return_value=True):
            backtester = MarketPortfolioBacktester(self.random_filepath)
            self.assertEqual(backtester.data, self.mock_data)

    def test_load_data_empty_file(self):
        with patch('builtins.open', return_value=io.StringIO("   ")), \
             patch('os.path.exists', return_value=True):
            backtester = MarketPortfolioBacktester(self.random_filepath)
            self.assertEqual(backtester.data, {})

    def test_load_data_file_not_found(self):
        with patch('os.path.exists', return_value=False):
            backtester = MarketPortfolioBacktester(self.random_filepath)
            self.assertEqual(backtester.data, {})

    def test_run_backtest_with_shifts(self):
        shifts = [random.uniform(-5.0, 5.0), random.uniform(-10.0, 10.0)]
        backtester = MarketPortfolioBacktester()
        backtester.data = self.mock_data

        result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol]["status"], "completed")
        self.assertEqual(result[self.symbol]["shifts_tested"], len(shifts))
        for shift in shifts:
            key = f"{self.symbol}_shift_{shift}"
            self.assertIn(key, result)
            self.assertEqual(result[key]["shift"], shift)
            self.assertEqual(result[key]["data_points"], len(self.mock_data[self.symbol]))

    def test_run_backtest_strategy_execution(self):
        strategy_params = {
            "buy_threshold": self.prices[0] + 1.0,
            "sell_threshold": self.prices[-1] + 10.0
        }
        backtester = MarketPortfolioBacktester()
        backtester.data = self.mock_data

        result = backtester.run_backtest(self.symbol, self.random_capital, strategy_params)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertIsInstance(result["final_portfolio_value"], float)
        self.assertIsInstance(result["total_trades"], int)
        self.assertIsInstance(result["pnl_percentage"], float)

    def test_run_backtest_empty_symbol_data(self):
        missing_symbol = f"MISSING_{uuid.uuid4().hex[:6]}"
        backtester = MarketPortfolioBacktester()
        backtester.data = {}

        result = backtester.run_backtest(missing_symbol, self.random_capital)
        self.assertEqual(result["final_portfolio_value"], self.random_capital)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["pnl_percentage"], 0.0)

    def test_calculate_maximum_drawdown(self):
        curve_len = random.randint(5, 20)
        equity_curve = [round(random.uniform(100.0, 1000.0), 2) for _ in range(curve_len)]
        backtester = MarketPortfolioBacktester()

        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)
        self.assertLessEqual(max_dd, 1.0)

    def test_calculate_maximum_drawdown_empty(self):
        backtester = MarketPortfolioBacktester()
        self.assertEqual(backtester.calculate_maximum_drawdown([]), 0.0)

    def test_simulate_historical_trades(self):
        allocation = round(random.uniform(100.0, 1000.0), 2)
        backtester = MarketPortfolioBacktester()
        backtester.data = self.mock_data

        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), len(self.prices))
        for i, trade in enumerate(trades):
            self.assertIn(trade["action"], ["BUY", "SELL"])
            self.assertEqual(trade["price"], self.prices[i])
            self.assertEqual(trade["allocation"], allocation)

    def test_get_backtest_summary(self):
        backtester = MarketPortfolioBacktester()
        backtester.data = self.mock_data

        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], len(self.prices))
        self.assertEqual(summary["status"], "ready")

    def test_market_backtester_alias(self):
        self.assertEqual(MarketBacktester, MarketPortfolioBacktester)

if __name__ == '__main__':
    unittest.main()