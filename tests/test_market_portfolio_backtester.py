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
        self.rand_filepath = f"test_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.initial_capital = round(random.uniform(1000.0, 50000.0), 2)

    def tearDown(self):
        if os.path.exists(self.rand_filepath):
            try:
                os.remove(self.rand_filepath)
            except OSError:
                pass

    def test_init_and_load_data_valid(self):
        test_data = {
            self.symbol: [
                {"price": round(random.uniform(10.0, 100.0), 2), "timestamp": random.randint(1000, 5000)}
            ]
        }
        with open(self.rand_filepath, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        backtester = MarketPortfolioBacktester(self.rand_filepath)
        self.assertIn(self.symbol, backtester.data)
        self.assertEqual(backtester.data[self.symbol][0]["price"], test_data[self.symbol][0]["price"])

    def test_load_data_empty_file(self):
        with open(self.rand_filepath, 'w', encoding='utf-8') as f:
            f.write("   ")

        backtester = MarketPortfolioBacktester(self.rand_filepath)
        self.assertEqual(backtester.data, {})

    def test_load_data_nonexistent_file(self):
        missing_path = f"missing_{uuid.uuid4().hex}.json"
        backtester = MarketPortfolioBacktester(missing_path)
        self.assertEqual(backtester.data, {})

    def test_load_data_malformed_json(self):
        with open(self.rand_filepath, 'w', encoding='utf-8') as f:
            f.write(uuid.uuid4().hex + "{ invalid json")

        backtester = MarketPortfolioBacktester(self.rand_filepath)
        self.assertEqual(backtester.data, {})

    def test_run_backtest_shift_mode(self):
        shifts = [random.randint(1, 10), random.randint(11, 20)]
        prices = [{"price": round(random.uniform(50.0, 150.0), 2), "timestamp": random.randint(100, 200)} for _ in range(5)]
        
        backtester = MarketPortfolioBacktester()
        backtester.data = {self.symbol: prices}

        result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol]["status"], "completed")
        self.assertEqual(result[self.symbol]["shifts_tested"], len(shifts))
        for shift in shifts:
            res_key = f"{self.symbol}_shift_{shift}"
            self.assertIn(res_key, result)
            self.assertEqual(result[res_key]["shift"], shift)
            self.assertEqual(result[res_key]["data_points"], len(prices))

    def test_run_backtest_capital_mode_empty_data(self):
        backtester = MarketPortfolioBacktester()
        backtester.data = {}

        result = backtester.run_backtest(self.symbol, self.initial_capital, {"buy_threshold": 10.0})
        self.assertEqual(result["final_portfolio_value"], self.initial_capital)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["pnl_percentage"], 0.0)

    def test_run_backtest_capital_mode_execution(self):
        p1 = round(random.uniform(10.0, 20.0), 2)
        p2 = round(random.uniform(80.0, 100.0), 2)
        prices = [
            {"price": p1, "timestamp": 1},
            {"price": p2, "timestamp": 2}
        ]
        backtester = MarketPortfolioBacktester()
        backtester.data = {self.symbol: prices}

        strategy_params = {
            "buy_threshold": p1,
            "sell_threshold": p2
        }

        result = backtester.run_backtest(self.symbol, self.initial_capital, strategy_params)
        self.assertGreater(result["total_trades"], 0)
        self.assertIsInstance(result["final_portfolio_value"], float)
        self.assertIsInstance(result["pnl_percentage"], float)

    def test_calculate_maximum_drawdown_empty(self):
        backtester = MarketPortfolioBacktester()
        dd = backtester.calculate_maximum_drawdown([])
        self.assertEqual(dd, 0.0)

    def test_calculate_maximum_drawdown_valid(self):
        curve = [round(random.uniform(100.0 + i * 10, 200.0 + i * 10), 2) for i in range(5)]
        curve[2] = curve[0] * 0.5
        backtester = MarketPortfolioBacktester()
        dd = backtester.calculate_maximum_drawdown(curve)
        self.assertGreater(dd, 0.0)
        self.assertIsInstance(dd, float)

    def test_simulate_historical_trades(self):
        prices = [{"price": round(random.uniform(1.0, 50.0), 2), "timestamp": random.randint(10, 100)} for _ in range(3)]
        backtester = MarketPortfolioBacktester()
        backtester.data = {self.symbol: prices}
        allocation = round(random.uniform(0.1, 1.0), 2)

        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), len(prices))
        for i, trade in enumerate(trades):
            self.assertEqual(trade["price"], prices[i]["price"])
            self.assertEqual(trade["allocation"], allocation)
            self.assertEqual(trade["timestamp"], prices[i]["timestamp"])
            self.assertIn(trade["action"], ["BUY", "SELL"])

    def test_get_backtest_summary(self):
        prices = [{"price": round(random.uniform(5.0, 50.0), 2)} for _ in range(4)]
        backtester = MarketPortfolioBacktester()
        backtester.data = {self.symbol: prices}

        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], 4)
        self.assertEqual(summary["status"], "ready")

    def test_market_backtester_alias(self):
        self.assertEqual(MarketBacktester, MarketPortfolioBacktester)

    def test_io_stream_loading_mock(self):
        rand_content = json.dumps({self.symbol: [{"price": 123.45}]})
        mock_file = io.BytesIO(rand_content.encode('utf-8'))
        
        with patch('builtins.open', return_value=mock_file):
            backtester = MarketPortfolioBacktester(self.rand_filepath)
            self.assertIn(self.symbol, backtester.data)

if __name__ == '__main__':
    unittest.main()