import unittest
import os
import uuid
import random
from skills.market_portfolio_backtest_optimizer_bridge import PortfolioBacktestOptimizerBridge

class TestPortfolioBacktestOptimizerBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"

        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = random.randint(5, 30)
        self.percentage = round(random.uniform(1.0, 15.0), 2)
        self.allocation = round(random.uniform(100.0, 1000.0), 2)

        test_data = {
            self.symbol: [
                {"price": 100.0 + random.uniform(0.0, 5.0)},
                {"price": 105.0},
                {"price": 102.0},
                {"price": 110.0},
                {"price": 108.0}
            ]
        }

        import json
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        self.bridge = PortfolioBacktestOptimizerBridge(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_run_bridge_pipeline_integration(self):
        result = self.bridge.run_bridge_pipeline(
            symbol=self.symbol,
            shifts=self.shifts,
            percentage=self.percentage
        )

        self.assertIsInstance(result, dict)
        self.assertIn("optimizer_result", result)
        self.assertIn("backtest_summary", result)
        self.assertIn("maximum_drawdown", result)
        self.assertIn("equity_curve", result)

    def test_evaluate_bridge_resilience_integration(self):
        resilience_res = self.bridge.evaluate_bridge_resilience(
            symbol=self.symbol,
            shifts=self.shifts
        )

        self.assertIsInstance(resilience_res, (dict, list, float, int))

    def test_simulate_bridge_historical_trades_integration(self):
        trades = self.bridge.simulate_bridge_historical_trades(
            symbol=self.symbol,
            allocation=self.allocation
        )

        self.assertIsInstance(trades, list)

    def test_optimize_and_backtest_integration(self):
        pipeline_res = self.bridge.optimize_and_backtest(
            symbol=self.symbol,
            shifts=self.shifts,
            percentage=self.percentage
        )

        self.assertIsInstance(pipeline_res, dict)
        self.assertTrue(len(pipeline_res) > 0)

if __name__ == '__main__':
    unittest.main()