import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4()}.json")
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_storage_creation_and_comprehensive_evaluation(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        initial_capital = round(random.uniform(10000.0, 100000.0), 2)
        strategy_params = {
            "hedge_ratio": round(random.uniform(0.1, 0.9), 2),
            "max_drawdown_limit": round(random.uniform(0.05, 0.25), 2)
        }

        self.assertFalse(os.path.exists(self.storage_file))

        result = self.bridge.run_comprehensive_evaluation(symbol, initial_capital, strategy_params)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_evaluate_strategy_backtest_flow(self):
        symbol = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        strategy_params = {
            "threshold": round(random.uniform(1.0, 5.0), 2)
        }

        eval_result = self.bridge.evaluate_strategy_backtest(symbol, initial_capital, strategy_params)

        self.assertIn("backtest_summary", eval_result)
        self.assertIn("performance_metrics", eval_result)
        self.assertIn("performance_evaluation", eval_result)

        perf_eval = self.bridge.evaluate_backtest_performance(symbol)
        self.assertIn("backtest_summary", perf_eval)
        self.assertIn("performance_metrics", perf_eval)
        self.assertIn("performance_evaluation", perf_eval)

if __name__ == "__main__":
    unittest.main()