import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_backtest_storage_{self.random_suffix}.json"
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_run_comprehensive_evaluation_integration(self):
        initial_capital = round(random.uniform(10000.0, 100000.0), 2)
        strategy_params = {
            "stop_loss": round(random.uniform(0.01, 0.05), 4),
            "take_profit": round(random.uniform(0.05, 0.15), 4),
            "leverage": random.randint(1, 5)
        }

        result = self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=initial_capital,
            strategy_params=strategy_params
        )

        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertGreater(os.path.getsize(self.storage_file), 0)

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_evaluate_strategy_backtest_integration(self):
        initial_capital = round(random.uniform(5000.0, 50000.0), 2)
        strategy_params = {
            "hedge_ratio": round(random.uniform(0.1, 0.9), 2),
            "rebalance_threshold": round(random.uniform(0.02, 0.1), 4)
        }

        result = self.bridge.evaluate_strategy_backtest(
            symbol=self.symbol,
            initial_capital=initial_capital,
            strategy_params=strategy_params
        )

        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

        self.assertTrue(os.path.exists(self.storage_file))

    def test_evaluate_backtest_performance_integration(self):
        result = self.bridge.evaluate_backtest_performance(symbol=self.symbol)

        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()