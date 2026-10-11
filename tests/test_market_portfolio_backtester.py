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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.temp_filepath = f"test_data_{uuid.uuid4().hex}.json"
        self.random_capital = round(random.uniform(1000.0, 50000.0), 2)
        self.random_shift = random.uniform(1.0, 15.0)

    def tearDown(self):
        if os.path.exists(self.temp_filepath):
            try:
                os.remove(self.temp_filepath)
            except OSError:
                pass

    def test_load_data_nonexistent_file(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        tester = MarketPortfolioBacktester(non_existent)
        self.assertEqual(tester.data, {})

    def test_load_data_empty_file(self):
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            f.write("   ")
        tester = MarketPortfolioBacktester(self.temp_filepath)
        self.assertEqual(tester.data, {})

    def test_load_data_valid_json(self):
        dummy_price = round(random.uniform(10.0, 500.0), 2)
        payload = {self.symbol: [{"price": dummy_price, "timestamp": random.randint(100000, 999999)}]}
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        
        tester = MarketPortfolioBacktester(self.temp_filepath)
        self.assertIn(self.symbol, tester.data)
        self.assertEqual(tester.data[self.symbol][0]["price"], dummy_price)

    def test_load_data_invalid_json(self):
        garbage = f"invalid_json_{uuid.uuid4().hex}"
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            f.write(garbage)
        tester = MarketPortfolioBacktester(self.temp_filepath)
        self.assertEqual(tester.data, {})

    def test_run_backtest_integration_signature_shifts(self):
        shifts = [self.random_shift, self.random_shift * 2]
        payload = {
            self.symbol: [
                {"price": 100.0, "timestamp": 1},
                {"price": 105.0, "timestamp": 2}
            ]
        }
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        tester = MarketPortfolioBacktester(self.temp_filepath)
        res = tester.run_backtest(self.symbol, shifts)
        
        self.assertIn(self.symbol, res)
        self.assertEqual(res[self.symbol]["status"], "completed")
        self.assertEqual(res[self.symbol]["shifts_tested"], len(shifts))
        for shift in shifts:
            key = f"{self.symbol}_shift_{shift}"
            self.assertIn(key, res)
            self.assertEqual(res[key]["shift"], shift)

    def test_run_backtest_unit_empty_symbol_data(self):
        tester = MarketPortfolioBacktester()
        res = tester.run_backtest(self.symbol, self.random_capital)
        self.assertEqual(res["final_portfolio_value"], self.random_capital)
        self.assertEqual(res["total_trades"], 0)
        self.assertEqual(res["pnl_percentage"], 0.0)

    def test_run_backtest_unit_execution_logic(self):
        buy_pr = round(random.uniform(10.0, 50.0), 2)
        sell_pr = round(random.uniform(60.0, 100.0), 2)
        
        payload = {
            self.symbol: [
                {"price": buy_pr, "timestamp": 100},
                {"price": sell_pr, "timestamp": 200}
            ]
        }
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        tester = MarketPortfolioBacktester(self.temp_filepath)
        strategy_params = {
            "buy_threshold": buy_pr,
            "sell_threshold": sell_pr
        }
        
        res = tester.run_backtest(self.symbol, self.random_capital, strategy_params)
        self.assertGreater(res["total_trades"], 0)
        self.assertIsInstance(res["final_portfolio_value"], float)
        self.assertIsInstance(res["pnl_percentage"], float)

    def test_calculate_maximum_drawdown_empty(self):
        tester = MarketPortfolioBacktester()
        dd = tester.calculate_maximum_drawdown([])
        self.assertEqual(dd, 0.0)

    def test_calculate_maximum_drawdown_calculation(self):
        curve = [100.0, 120.0, 90.0, 110.0, 80.0]
        tester = MarketPortfolioBacktester()
        dd = tester.calculate_maximum_drawdown(curve)
        expected_dd = (120.0 - 80.0) / 120.0
        self.assertAlmostEqual(dd, expected_dd, places=5)

    def test_simulate_historical_trades(self):
        price_val = round(random.uniform(5.0, 500.0), 2)
        alloc_val = round(random.uniform(0.1, 1.0), 2)
        ts_val = random.randint(1000000, 9999999)
        
        payload = {
            self.symbol: [
                {"price": price_val, "timestamp": ts_val},
                {"price": price_val + 10, "timestamp": ts_val + 50}
            ]
        }
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        tester = MarketPortfolioBacktester(self.temp_filepath)
        trades = tester.simulate_historical_trades(self.symbol, alloc_val)
        
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["action"], "BUY")
        self.assertEqual(trades[0]["price"], price_val)
        self.assertEqual(trades[0]["allocation"], alloc_val)
        self.assertEqual(trades[0]["timestamp"], ts_val)
        self.assertEqual(trades[1]["action"], "SELL")

    def test_get_backtest_summary(self):
        records_count = random.randint(1, 10)
        symbol_records = [{"price": float(i), "timestamp": i} for i in range(records_count)]
        payload = {self.symbol: symbol_records}
        
        with open(self.temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        tester = MarketPortfolioBacktester(self.temp_filepath)
        summary = tester.get_backtest_summary(self.symbol)
        
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], records_count)
        self.assertEqual(summary["status"], "ready")

    def test_market_backtester_alias(self):
        self.assertEqual(MarketBacktester, MarketPortfolioBacktester)

    def test_load_data_io_error_handling(self):
        garbage_bytes = f"corrupted_{uuid.uuid4().hex}".encode('utf-8')
        mock_file = io.BytesIO(garbage_bytes)
        
        with patch('builtins.open', return_value=mock_file):
            tester = MarketPortfolioBacktester(self.temp_filepath)
            data = tester.load_data(self.temp_filepath)
            self.assertEqual(data, {})