import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_storage_{uuid.uuid4().hex}.json")
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_storage_creation_and_comprehensive_evaluation(self):
        initial_capital = float(random.randint(10000, 1000000))
        strategy_params = {
            "risk_tolerance": round(random.uniform(0.1, 0.9), 2),
            "leverage": round(random.uniform(1.0, 3.0), 2)
        }

        result = self.bridge.run_comprehensive_evaluation(self.symbol, initial_capital, strategy_params)

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_evaluate_strategy_backtest_flow(self):
        initial_capital = float(random.randint(5000, 500000))
        strategy_params = {
            "stop_loss": round(random.uniform(0.01, 0.1), 3),
            "take_profit": round(random.uniform(0.02, 0.2), 3)
        }

        result = self.bridge.evaluate_strategy_backtest(self.symbol, initial_capital, strategy_params)

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

    def test_evaluate_backtest_performance_existing_storage(self):
        with open(self.storage_file, "w") as f:
            json.dump({self.symbol: {"initialized": True, "salt": uuid.uuid4().hex}}, f)

        result = self.bridge.evaluate_backtest_performance(self.symbol)

        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

if __name__ == "__main__":
    unittest.main()