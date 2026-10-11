import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester
from skills.db_storage import MarketParser

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_data_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_filepath = os.path.join(self.test_dir, f"market_data_{uuid.uuid4().hex}.json")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price_1 = round(random.uniform(10.0, 50.0), 2)
        self.random_price_2 = round(random.uniform(51.0, 100.0), 2)
        
        self.mock_data = {
            self.symbol: [
                {"timestamp": 1600000000, "price": self.random_price_1},
                {"timestamp": 1600086400, "price": self.random_price_2}
            ]
        }
        
        with open(self.test_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.mock_data, f)

    def tearDown(self):
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_market_portfolio_backtester_integration(self):
        backtester = MarketPortfolioBacktester(filepath=self.test_filepath)
        
        self.assertEqual(backtester.filepath, self.test_filepath)
        self.assertIn(self.symbol, backtester.data)

        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], 2)
        self.assertEqual(summary["status"], "ready")

        shifts = [random.randint(1, 5), random.randint(6, 10)]
        shift_result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, shift_result)
        self.assertEqual(shift_result[self.symbol]["status"], "completed")
        self.assertEqual(shift_result[self.symbol]["shifts_tested"], len(shifts))

        initial_capital = round(random.uniform(1000.0, 5000.0), 2)
        strategy_params = {
            "buy_threshold": self.random_price_1 + 1.0,
            "sell_threshold": self.random_price_2 - 1.0
        }
        run_res = backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", run_res)
        self.assertIn("total_trades", run_res)
        self.assertIn("pnl_percentage", run_res)

        equity_curve = [initial_capital, initial_capital * 1.1, initial_capital * 0.9, initial_capital * 1.2]
        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertGreaterEqual(max_dd, 0.0)

        allocation = round(random.uniform(100.0, 1000.0), 2)
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), len(self.mock_data[self.symbol]))
        for trade in trades:
            self.assertEqual(trade["allocation"], allocation)
            self.assertIn(trade["action"], ["BUY", "SELL"])

        alias_backtester = MarketBacktester(filepath=self.test_filepath)
        self.assertIsInstance(alias_backtester, MarketPortfolioBacktester)

if __name__ == '__main__':
    unittest.main()