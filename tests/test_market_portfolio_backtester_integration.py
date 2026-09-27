import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_scenario_simulator import MarketPortfolioScenarioSimulator

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.filename = f"test_data_{uuid.uuid4().hex}.json"
        
        self.price_1 = round(random.uniform(10.0, 50.0), 2)
        self.price_2 = round(random.uniform(51.0, 100.0), 2)
        self.price_3 = round(random.uniform(5.0, 9.0), 2)
        
        self.test_data = {
            self.symbol: [
                {"timestamp": 1000, "price": self.price_1},
                {"timestamp": 2000, "price": self.price_2},
                {"timestamp": 3000, "price": self.price_3}
            ]
        }

        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f)

        self.backtester = MarketPortfolioBacktester(filepath=self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_backtester_scenario_simulator_integration(self):
        self.assertIsInstance(self.backtester.scenario_simulator, MarketPortfolioScenarioSimulator)

        initial_capital = round(random.uniform(1000.0, 10000.0), 2)
        buy_thresh = self.price_1 + round(random.uniform(1.0, 5.0), 2)
        sell_thresh = self.price_2 + round(random.uniform(1.0, 5.0), 2)

        strategy_params = {
            "buy_threshold": buy_thresh,
            "sell_threshold": sell_thresh
        }
        
        result = self.backtester.run_backtest(self.symbol, initial_capital, strategy_params)

        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertIsInstance(result["final_portfolio_value"], float)
        self.assertIsInstance(result["total_trades"], int)

        equity_curve = [initial_capital, result["final_portfolio_value"], initial_capital * 0.9]
        max_dd = self.backtester.calculate_maximum_drawdown(equity_curve)
        self.assertGreaterEqual(max_dd, 0.0)

        allocation = round(random.uniform(0.1, 1.0), 2)
        trades = self.backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), len(self.test_data[self.symbol]))
        
        summary = self.backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], len(self.test_data[self.symbol]))

if __name__ == '__main__':
    unittest.main()