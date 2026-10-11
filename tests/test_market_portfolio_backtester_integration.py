import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester
from skills.db_storage import MarketParser

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_filename = f"test_market_data_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        
        self.raw_data = {
            self.symbol: [
                {"timestamp": 1000000 + i * 100, "price": round(random.uniform(50.0, 150.0), 2)}
                for i in range(10)
            ]
        }
        
        with open(self.test_filename, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_backtester_and_market_parser_integration(self):
        backtester = MarketPortfolioBacktester(filepath=self.test_filename)
        
        self.assertIn(self.symbol, backtester.data)
        
        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], len(self.raw_data[self.symbol]))
        self.assertEqual(summary["status"], "ready")

        initial_capital = float(random.randint(5000, 15000))
        strategy_params = {
            "buy_threshold": float(random.uniform(60.0, 80.0)),
            "sell_threshold": float(random.uniform(100.0, 130.0))
        }

        result = backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertIsInstance(result["final_portfolio_value"], float)

        shifts = [random.randint(1, 5), random.randint(6, 10)]
        shift_result = backtester.run_backtest(self.symbol, shifts)
        self.assertIn(self.symbol, shift_result)
        self.assertEqual(shift_result[self.symbol]["status"], "completed")

        equity_curve = [item["price"] for item in self.raw_data[self.symbol]]
        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertGreaterEqual(max_dd, 0.0)

        allocation = float(random.uniform(0.1, 1.0))
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertEqual(len(trades), len(self.raw_data[self.symbol]))
        self.assertEqual(trades[0]["allocation"], allocation)

        market_parser = MarketParser()
        self.assertIsNotNone(market_parser)

if __name__ == '__main__':
    unittest.main()