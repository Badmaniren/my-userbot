import unittest
import os
import json
import uuid
import random
from skills.market_parser import MarketParser
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_filename = f"test_market_data_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
        self.random_prices = [round(random.uniform(10.0, 500.0), 2) for _ in range(random.randint(5, 15))]
        self.raw_data = {
            self.symbol: [{"price": p, "timestamp": 1600000000 + i * 3600} for i, p in enumerate(self.random_prices)]
        }
        
        with open(self.test_filename, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_market_portfolio_backtester_integration_pipeline(self):
        parser = MarketParser(storage_file=self.test_filename)
        loaded_data = parser.load_data(self.test_filename)
        self.assertIn(self.symbol, loaded_data)
        
        backtester = MarketPortfolioBacktester(filepath=self.test_filename)
        self.assertEqual(backtester.data, loaded_data)
        
        alias_backtester = MarketBacktester(filepath=self.test_filename)
        summary = alias_backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], len(self.random_prices))
        self.assertEqual(summary["status"], "ready")

        initial_capital = round(random.uniform(1000.0, 10000.0), 2)
        buy_threshold = min(self.random_prices) * 1.1
        sell_threshold = max(self.random_prices) * 0.95

        strategy_params = {
            "buy_threshold": buy_threshold,
            "sell_threshold": sell_threshold
        }

        backtest_result = backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", backtest_result)
        self.assertIn("total_trades", backtest_result)
        self.assertIn("pnl_percentage", backtest_result)
        self.assertIsInstance(backtest_result["final_portfolio_value"], float)

        shifts = [round(random.uniform(-0.1, 0.1), 2), round(random.uniform(-0.2, 0.2), 2)]
        shift_result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, shift_result)
        self.assertEqual(shift_result[self.symbol]["status"], "completed")
        self.assertEqual(shift_result[self.symbol]["shifts_tested"], len(shifts))

        equity_curve = [initial_capital, initial_capital * 1.05, initial_capital * 0.90, initial_capital * 1.15]
        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertGreaterEqual(max_dd, 0.0)
        self.assertLessEqual(max_dd, 1.0)

        allocation = round(random.uniform(100.0, 1000.0), 2)
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), len(self.random_prices))
        for trade in trades:
            self.assertIn("action", trade)
            self.assertIn("price", trade)
            self.assertIn("allocation", trade)
            self.assertIn("timestamp", trade)
            self.assertEqual(trade["allocation"], allocation)

if __name__ == "__main__":
    unittest.main()