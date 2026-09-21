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
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        
        parser = MarketParser(self.test_filename)
        self.test_prices = [
            round(random.uniform(10.0, 50.0), 2),
            round(random.uniform(51.0, 100.0), 2),
            round(random.uniform(5.0, 9.0), 2),
            round(random.uniform(101.0, 150.0), 2)
        ]
        
        for price in self.test_prices:
            parser.fetch_and_store(self.symbol, price)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_backtester_integration_with_db_storage(self):
        backtester = MarketPortfolioBacktester(self.test_filename)
        
        summary = backtester.get_backtest_summary(self.symbol)
        self.assertEqual(summary["symbol"], self.symbol)
        self.assertEqual(summary["total_records"], len(self.test_prices))
        self.assertEqual(summary["status"], "ready")

        initial_capital = float(random.randint(1000, 5000))
        strategy_params = {
            "buy_threshold": float(self.test_prices[0]),
            "sell_threshold": float(self.test_prices[3])
        }
        
        result = backtester.run_backtest(self.symbol, initial_capital, strategy_params)
        self.assertIn("final_portfolio_value", result)
        self.assertIn("total_trades", result)
        self.assertIn("pnl_percentage", result)
        self.assertIsInstance(result["final_portfolio_value"], float)

    def test_backtester_empty_slice_handling_no_suppression(self):
        empty_filename = f"empty_data_{uuid.uuid4()}.json"
        with open(empty_filename, 'w', encoding='utf-8') as f:
            f.write("")

        try:
            backtester = MarketPortfolioBacktester(empty_filename)
            non_existent_symbol = "UNKNOWN_SYM"
            result = backtester.run_backtest(non_existent_symbol, 1000.0)
            self.assertEqual(result["total_trades"], 0)
            self.assertEqual(result["pnl_percentage"], 0.0)
        finally:
            if os.path.exists(empty_filename):
                os.remove(empty_filename)

    def test_backtester_metrics_expansion(self):
        backtester = MarketPortfolioBacktester(self.test_filename)
        equity_curve = [100.0, float(random.randint(105, 120)), float(random.randint(90, 99)), float(random.randint(110, 130))]
        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)

        allocation = round(random.uniform(0.1, 1.0), 2)
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertIsInstance(trades, list)
        self.assertEqual(len(trades), len(self.test_prices))
        for trade in trades:
            self.assertIn("action", trade)
            self.assertIn("price", trade)
            self.assertIn("allocation", trade)

if __name__ == "__main__":
    unittest.main()