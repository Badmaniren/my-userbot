import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.db_storage import MarketParser

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_filename = f"test_market_data_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
        self.random_prices = [round(random.uniform(10.0, 100.0), 2) for _ in range(10)]
        self.market_data = {
            self.symbol: [
                {"price": p, "timestamp": 1600000000 + i * 3600} 
                for i, p in enumerate(self.random_prices)
            ]
        }
        
        with open(self.test_filename, 'w', encoding='utf-8') as f:
            json.dump(self.market_data, f)
            
        self.backtester = MarketPortfolioBacktester(self.test_filename)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_backtest_run_and_predictive_integration(self):
        initial_capital = round(random.uniform(1000.0, 5000.0), 2)
        buy_thresh = self.random_prices[2]
        sell_thresh = self.random_prices[7]
        
        strategy_params = {
            "buy_threshold": buy_thresh,
            "sell_threshold": sell_thresh
        }
        
        result = self.backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertIsInstance(result["final_portfolio_value"], float)
        self.assertGreaterEqual(result["total_trades"], 0)

    def test_shifts_execution_and_stress_compatibility(self):
        shift_count = random.randint(2, 5)
        shifts = [random.randint(1, 10) for _ in range(shift_count)]
        
        result = self.backtester.run_backtest(self.symbol, shifts)
        
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol]["status"], "completed")
        self.assertEqual(result[self.symbol]["shifts_tested"], shift_count)

    def test_maximum_drawdown_calculation(self):
        synthetic_curve = [round(random.uniform(50.0, 150.0), 2) for _ in range(15)]
        max_dd = self.backtester.calculate_maximum_drawdown(synthetic_curve)
        
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)
        self.assertLessEqual(max_dd, 1.0)

    def test_historical_trades_simulation(self):
        allocation = round(random.uniform(100.0, 1000.0), 2)
        trades = self.backtester.simulate_historical_trades(self.symbol, allocation)
        
        self.assertIsInstance(trades, list)
        self.assertEqual(len(trades), len(self.random_prices))
        for trade in trades:
            self.assertIn("action", trade)
            self.assertIn("price", trade)
            self.assertEqual(trade["allocation"], allocation)

    def test_backtest_summary(self):
        summary = self.backtester.get_backtest_summary(self.symbol)
        
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], len(self.random_prices))
        self.assertEqual(summary["status"], "ready")

if __name__ == '__main__':
    unittest.main()