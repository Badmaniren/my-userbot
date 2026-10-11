import unittest
from unittest.mock import patch
import os
import json
import io
import uuid
import random
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester

class TestMarketPortfolioBacktester(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.rand_filepath = f"{uuid.uuid4().hex}.json"
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)

    def tearDown(self):
        if os.path.exists(self.rand_filepath):
            try:
                os.remove(self.rand_filepath)
            except OSError:
                pass

    def test_load_data_valid_json(self):
        test_data = {
            self.rand_symbol: [
                {"price": round(random.uniform(10.0, 100.0), 2), "timestamp": random.randint(100000, 200000)}
            ]
        }
        with open(self.rand_filepath, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        tester = MarketPortfolioBacktester(self.rand_filepath)
        loaded = tester.load_data()
        self.assertIn(self.rand_symbol, loaded)
        self.assertEqual(loaded[self.rand_symbol][0]["price"], test_data[self.rand_symbol][0]["price"])

    def test_load_data_empty_file_and_missing(self):
        with open(self.rand_filepath, 'w', encoding='utf-8') as f:
            f.write("   ")

        tester = MarketPortfolioBacktester(self.rand_filepath)
        self.assertEqual(tester.data, {})

        missing_path = f"{uuid.uuid4().hex}.json"
        tester_missing = MarketPortfolioBacktester(missing_path)
        self.assertEqual(tester_missing.load_data(), {})

    def test_load_data_exception_handling(self):
        with open(self.rand_filepath, 'w', encoding='utf-8') as f:
            f.write("{invalid_json_syntax")

        with patch('builtins.open', return_value=io.StringIO("broken")):
            tester = MarketPortfolioBacktester()
            res = tester.load_data(self.rand_filepath)
            self.assertEqual(res, {})

    def test_run_backtest_with_shifts(self):
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        prices = [round(random.uniform(50.0, 150.0), 2) for _ in range(10)]
        
        tester = MarketPortfolioBacktester()
        tester.data = {self.rand_symbol: [{"price": p} for p in prices]}

        result = tester.run_backtest(self.rand_symbol, shifts)
        self.assertIn(self.rand_symbol, result)
        self.assertEqual(result[self.rand_symbol]["status"], "completed")
        self.assertEqual(result[self.rand_symbol]["shifts_tested"], len(shifts))
        
        for shift in shifts:
            key = f"{self.rand_symbol}_shift_{shift}"
            self.assertIn(key, result)
            self.assertEqual(result[key]["shift"], shift)
            self.assertEqual(result[key]["data_points"], len(prices))

    def test_run_backtest_execution_logic(self):
        p1 = round(random.uniform(10.0, 30.0), 2)
        p2 = round(random.uniform(40.0, 70.0), 2)
        p3 = round(random.uniform(80.0, 120.0), 2)

        tester = MarketPortfolioBacktester()
        tester.data = {
            self.rand_symbol: [
                {"price": p1},
                {"price": p2},
                {"price": p3}
            ]
        }

        strategy_params = {
            "buy_threshold": p1 + 0.5,
            "sell_threshold": p3 - 0.5
        }

        result = tester.run_backtest(self.rand_symbol, self.initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertGreaterEqual(result["total_trades"], 0)

    def test_run_backtest_empty_symbol_data(self):
        tester = MarketPortfolioBacktester()
        tester.data = {}
        result = tester.run_backtest(self.rand_symbol, self.initial_capital)
        self.assertEqual(result["final_portfolio_value"], self.initial_capital)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["pnl_percentage"], 0.0)

    def test_calculate_maximum_drawdown(self):
        curve = [
            round(random.uniform(100.0, 120.0), 2),
            round(random.uniform(80.0, 99.0), 2),
            round(random.uniform(121.0, 150.0), 2),
            round(random.uniform(60.0, 79.0), 2)
        ]
        tester = MarketPortfolioBacktester()
        max_dd = tester.calculate_maximum_drawdown(curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)

        empty_dd = tester.calculate_maximum_drawdown([])
        self.assertEqual(empty_dd, 0.0)

    def test_simulate_historical_trades(self):
        ts = random.randint(1000000, 9999999)
        price = round(random.uniform(10.0, 500.0), 2)
        allocation = round(random.uniform(0.1, 1.0), 2)

        tester = MarketPortfolioBacktester()
        tester.data = {
            self.rand_symbol: [
                {"price": price, "timestamp": ts},
                {"price": price + 5.0, "timestamp": ts + 10}
            ]
        }

        trades = tester.simulate_historical_trades(self.rand_symbol, allocation)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["action"], "BUY")
        self.assertEqual(trades[1]["action"], "SELL")
        self.assertEqual(trades[0]["allocation"], allocation)
        self.assertEqual(trades[0]["timestamp"], ts)

    def test_get_backtest_summary(self):
        record_count = random.randint(1, 10)
        tester = MarketPortfolioBacktester()
        tester.data = {
            self.rand_symbol: [{"price": random.uniform(1, 100)} for _ in range(record_count)]
        }

        summary = tester.get_backtest_summary(self.rand_symbol)
        self.assertEqual(summary["symbol"], self.rand_symbol)
        self.assertEqual(summary["total_records"], record_count)
        self.assertEqual(summary["status"], "ready")

    def test_alias_market_backtester(self):
        self.assertIs(MarketBacktester, MarketPortfolioBacktester)

if __name__ == '__main__':
    unittest.main()