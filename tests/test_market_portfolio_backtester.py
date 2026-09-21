import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import json
import uuid
import random
import io
import sys

from skills.market_portfolio_backtester import MarketPortfolioBacktester

class TestMarketPortfolioBacktester(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
        self.sample_data = {
            self.symbol: [
                {"timestamp": 1000, "price": 100.0},
                {"timestamp": 2000, "price": 105.0},
                {"timestamp": 3000, "price": 102.0},
                {"timestamp": 4000, "price": 110.0},
                {"timestamp": 5000, "price": 108.0}
            ]
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_and_load_data(self):
        rand_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        rand_symbol = f"T_{uuid.uuid4().hex[:4]}"
        inner_data = {rand_symbol: [{"timestamp": random.randint(1, 100), "price": random.uniform(10, 50)}]}
        with open(rand_file, 'w', encoding='utf-8') as f:
            json.dump(inner_data, f)

        backtester = MarketPortfolioBacktester(rand_file)
        loaded = backtester.load_data(rand_file)
        self.assertIn(rand_symbol, loaded)
        self.assertEqual(loaded[rand_symbol][0]["price"], inner_data[rand_symbol][0]["price"])

    def test_load_data_missing_file(self):
        missing_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        backtester = MarketPortfolioBacktester(missing_file)
        data = backtester.load_data(missing_file)
        self.assertEqual(data, {})

    def test_run_backtest_strategy(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        initial_capital = round(random.uniform(1000.0, 5000.0), 2)
        strategy_params = {
            "buy_threshold": round(random.uniform(100.0, 103.0), 2),
            "sell_threshold": round(random.uniform(106.0, 112.0), 2)
        }
        
        result = backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        self.assertIsInstance(result, dict)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)

    def test_run_backtest_nonexistent_symbol(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        fake_symbol = f"MISSING_{uuid.uuid4().hex[:4]}"
        capital = round(random.uniform(500, 1500), 2)
        result = backtester.run_backtest(fake_symbol, capital, {})
        self.assertEqual(result.get("final_portfolio_value"), capital)
        self.assertEqual(result.get("total_trades"), 0)

    def test_calculate_drawdown(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        equity_curve = [
            random.uniform(100, 110),
            random.uniform(115, 125),
            random.uniform(90, 99),
            random.uniform(105, 115)
        ]
        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)

    def test_calculate_drawdown_empty(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        max_dd = backtester.calculate_maximum_drawdown([])
        self.assertEqual(max_dd, 0.0)

    def test_simulate_historical_trades(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        allocation = round(random.uniform(0.1, 1.0), 2)
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertIsInstance(trades, list)
        if len(trades) > 0:
            self.assertIn("action", trades[0])
            self.assertIn("price", trades[0])

    def test_get_backtest_summary(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        summary = backtester.get_backtest_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn("symbol", summary)
        self.assertEqual(summary["symbol"], self.symbol)

    def test_stream_data_io_mock(self):
        backtester = MarketPortfolioBacktester(self.storage_file)
        random_bytes = f'{{"{self.symbol}": [{{"timestamp": 9999, "price": 123.45}}]}}'.encode('utf-8')
        mock_file_obj = io.BytesIO(random_bytes)
        
        with patch('builtins.open', return_value=mock_file_obj):
            data = backtester.load_data(self.storage_file)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol][0]["price"], 123.45)