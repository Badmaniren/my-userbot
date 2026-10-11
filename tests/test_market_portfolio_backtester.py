import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester

class TestMarketPortfolioBacktester(unittest.TestCase):
    def setUp(self):
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_filepath = f"test_{uuid.uuid4().hex}.json"
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)
        self.buy_threshold = round(random.uniform(10.0, 50.0), 2)
        self.sell_threshold = round(random.uniform(100.0, 200.0), 2)
        
        self.market_data = {
            self.random_symbol: [
                {"timestamp": 1600000000 + i * 86400, "price": round(random.uniform(self.buy_threshold - 5, self.sell_threshold + 5), 2)}
                for i in range(random.randint(5, 15))
            ]
        }

    def tearDown(self):
        if os.path.exists(self.random_filepath):
            try:
                os.remove(self.random_filepath)
            except OSError:
                pass

    def test_load_data_valid_file(self):
        json_content = json.dumps(self.market_data)
        with open(self.random_filepath, 'w', encoding='utf-8') as f:
            f.write(json_content)

        tester = MarketPortfolioBacktester(filepath=self.random_filepath)
        self.assertIn(self.random_symbol, tester.data)
        self.assertEqual(len(tester.data[self.random_symbol]), len(self.market_data[self.random_symbol]))

    def test_load_data_empty_file(self):
        with open(self.random_filepath, 'w', encoding='utf-8') as f:
            f.write("   ")

        tester = MarketPortfolioBacktester(filepath=self.random_filepath)
        self.assertEqual(tester.data, {})

    def test_load_data_nonexistent_file(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        tester = MarketPortfolioBacktester(filepath=non_existent)
        self.assertEqual(tester.data, {})

    def test_load_data_corrupted_json(self):
        with open(self.random_filepath, 'w', encoding='utf-8') as f:
            f.write("{invalid_json_format")

        tester = MarketPortfolioBacktester(filepath=self.random_filepath)
        self.assertEqual(tester.data, {})

    def test_run_backtest_with_shifts(self):
        tester = MarketPortfolioBacktester()
        tester.data = self.market_data
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        
        result = tester.run_backtest(self.random_symbol, shifts)
        self.assertIn(self.random_symbol, result)
        self.assertEqual(result[self.random_symbol]["status"], "completed")
        self.assertEqual(result[self.random_symbol]["shifts_tested"], len(shifts))
        
        for shift in shifts:
            res_key = f"{self.random_symbol}_shift_{shift}"
            self.assertIn(res_key, result)
            self.assertEqual(result[res_key]["shift"], shift)

    def test_run_backtest_with_capital_and_strategy(self):
        tester = MarketPortfolioBacktester()
        tester.data = self.market_data
        strategy_params = {
            "buy_threshold": self.buy_threshold,
            "sell_threshold": self.sell_threshold
        }

        result = tester.run_backtest(self.random_symbol, self.initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertIsInstance(result["final_portfolio_value"], float)
        self.assertIsInstance(result["total_trades"], int)
        self.assertIsInstance(result["pnl_percentage"], float)

    def test_run_backtest_empty_symbol_data(self):
        tester = MarketPortfolioBacktester()
        empty_symbol = f"EMPTY_{uuid.uuid4().hex[:6]}"
        tester.data = {}

        result = tester.run_backtest(empty_symbol, self.initial_capital)
        self.assertEqual(result["final_portfolio_value"], self.initial_capital)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["pnl_percentage"], 0.0)

    def test_calculate_maximum_drawdown(self):
        tester = MarketPortfolioBacktester()
        curve_len = random.randint(5, 20)
        base_val = random.uniform(100.0, 500.0)
        equity_curve = [base_val + random.uniform(-20.0, 50.0) for _ in range(curve_len)]
        
        max_dd = tester.calculate_maximum_drawdown(equity_curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)
        self.assertLessEqual(max_dd, 1.0)

    def test_calculate_maximum_drawdown_empty(self):
        tester = MarketPortfolioBacktester()
        self.assertEqual(tester.calculate_maximum_drawdown([]), 0.0)

    def test_simulate_historical_trades(self):
        tester = MarketPortfolioBacktester()
        tester.data = self.market_data
        allocation = round(random.uniform(0.1, 1.0), 2)

        trades = tester.simulate_historical_trades(self.random_symbol, allocation)
        self.assertIsInstance(trades, list)
        self.assertEqual(len(trades), len(self.market_data[self.random_symbol]))
        if trades:
            self.assertIn(trades[0]["action"], ["BUY", "SELL"])
            self.assertEqual(trades[0]["allocation"], allocation)

    def test_get_backtest_summary(self):
        tester = MarketPortfolioBacktester()
        tester.data = self.market_data

        summary = tester.get_backtest_summary(self.random_symbol)
        self.assertEqual(summary["symbol"], self.random_symbol)
        self.assertEqual(summary["total_records"], len(self.market_data[self.random_symbol]))
        self.assertEqual(summary["status"], "ready")

    def test_market_backtester_alias(self):
        self.assertIs(MarketBacktester, MarketPortfolioBacktester)

if __name__ == '__main__':
    unittest.main()