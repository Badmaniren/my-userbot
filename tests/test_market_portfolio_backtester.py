import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester

class TestMarketPortfolioBacktesterStrict(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.filename = os.path.join(self.test_dir, f"market_data_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.alternative_symbol = f"SYM_{random.randint(10000, 99999)}"

    def tearDown(self):
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                for root, dirs, files in os.walk(self.test_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_load_data_valid_json(self):
        price_val = round(random.uniform(10.0, 500.0), 2)
        payload = {self.symbol: [{"timestamp": random.randint(1000, 5000), "price": price_val}]}
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        backtester = MarketPortfolioBacktester(self.filename)
        self.assertIn(self.symbol, backtester.data)
        self.assertEqual(backtester.data[self.symbol][0]["price"], price_val)

    def test_load_data_stream_format(self):
        price_1 = round(random.uniform(10.0, 100.0), 2)
        price_2 = round(random.uniform(101.0, 200.0), 2)
        line1 = json.dumps({self.symbol: [{"timestamp": 100, "price": price_1}]})
        line2 = json.dumps({self.symbol: [{"timestamp": 200, "price": price_2}]})

        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(line1 + "\n" + line2 + "\n")

        backtester = MarketPortfolioBacktester(self.filename)
        self.assertIn(self.symbol, backtester.data)
        self.assertEqual(len(backtester.data[self.symbol]), 2)
        self.assertEqual(backtester.data[self.symbol][0]["price"], price_1)
        self.assertEqual(backtester.data[self.symbol][1]["price"], price_2)

    def test_load_data_empty_and_invalid_paths(self):
        empty_file = os.path.join(self.test_dir, f"empty_{uuid.uuid4().hex}.json")
        with open(empty_file, 'w', encoding='utf-8') as f:
            f.write("")

        backtester = MarketPortfolioBacktester(empty_file)
        self.assertEqual(backtester.data, {})

        non_existent = os.path.join(self.test_dir, f"non_{uuid.uuid4().hex}.json")
        backtester_missing = MarketPortfolioBacktester(non_existent)
        self.assertEqual(backtester_missing.data, {})

    def test_run_backtest_list_shifts(self):
        shifts = [random.uniform(0.01, 0.05), random.uniform(0.06, 0.10)]
        payload = {self.symbol: [{"timestamp": 1000, "price": 100.0}]}
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        backtester = MarketPortfolioBacktester(self.filename)
        result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol]["status"], "completed")
        self.assertEqual(result[self.symbol]["shifts_tested"], len(shifts))

    def test_run_backtest_capital_and_trades(self):
        initial_cap = round(random.uniform(1000.0, 5000.0), 2)
        p1 = round(random.uniform(10.0, 20.0), 2)
        p2 = round(random.uniform(50.0, 100.0), 2)

        payload = {
            self.symbol: [
                {"timestamp": 100, "price": p1},
                {"timestamp": 200, "price": p2}
            ]
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        backtester = MarketPortfolioBacktester(self.filename)
        strategy = {"buy_threshold": p1, "sell_threshold": p2}
        res = backtester.run_backtest(self.symbol, initial_cap, strategy)
        
        self.assertIn("final_portfolio_value", res)
        self.assertIn("total_trades", res)
        self.assertIn("pnl_percentage", res)
        self.assertIn("max_drawdown", res)
        self.assertIn("win_rate", res)
        self.assertGreaterEqual(res["total_trades"], 1)

    def test_run_backtest_missing_symbol(self):
        initial_cap = round(random.uniform(1000.0, 5000.0), 2)
        backtester = MarketPortfolioBacktester()
        res = backtester.run_backtest(self.alternative_symbol, initial_cap)
        self.assertEqual(res["final_portfolio_value"], initial_cap)
        self.assertEqual(res["total_trades"], 0)
        self.assertEqual(res["pnl_percentage"], 0.0)

    def test_calculate_maximum_drawdown(self):
        curve = [100.0, 110.0, 90.0, 95.0, 80.0, 120.0]
        backtester = MarketPortfolioBacktester()
        dd = backtester.calculate_maximum_drawdown(curve)
        self.assertAlmostEqual(dd, (110.0 - 80.0) / 110.0, places=4)

        empty_dd = backtester.calculate_maximum_drawdown([])
        self.assertEqual(empty_dd, 0.0)

    def test_simulate_historical_trades(self):
        p1 = round(random.uniform(10.0, 50.0), 2)
        p2 = round(random.uniform(51.0, 100.0), 2)
        payload = {
            self.symbol: [
                {"timestamp": 111, "price": p1},
                {"timestamp": 222, "price": p2}
            ]
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        backtester = MarketPortfolioBacktester(self.filename)
        allocation = round(random.uniform(0.1, 1.0), 2)
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["action"], "BUY")
        self.assertEqual(trades[1]["action"], "SELL")
        self.assertEqual(trades[0]["price"], p1)
        self.assertEqual(trades[0]["allocation"], allocation)

    def test_get_backtest_summary(self):
        payload = {
            self.symbol: [
                {"timestamp": 1, "price": 10.0},
                {"timestamp": 2, "price": 11.0},
                {"timestamp": 3, "price": 12.0}
            ]
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        backtester = MarketPortfolioBacktester(self.filename)
        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], 3)
        self.assertEqual(summary["status"], "ready")

    def test_market_backtester_alias(self):
        self.assertIs(MarketBacktester, MarketPortfolioBacktester)

    def test_load_data_with_io_mock(self):
        random_id = f"ID_{uuid.uuid4().hex}"
        stream_content = json.dumps({random_id: [{"price": 99.9}]})
        mock_file = io.StringIO(stream_content)
        
        with patch("builtins.open", return_value=mock_file):
            backtester = MarketPortfolioBacktester(self.filename)
            self.assertIn(random_id, backtester.data)
            self.assertEqual(backtester.data[random_id][0]["price"], 99.9)

    def test_validate_historical_data_negative_price(self):
        backtester = MarketPortfolioBacktester()
        invalid_data = [{"price": 10.0}, {"price": -5.0}]
        with self.assertRaises(ValueError):
            backtester.validate_historical_data(invalid_data)

    def test_validate_historical_data_invalid_type(self):
        backtester = MarketPortfolioBacktester()
        with self.assertRaises(TypeError):
            backtester.validate_historical_data("invalid_type")
