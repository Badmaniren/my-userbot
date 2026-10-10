import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_file = os.path.join(self.test_dir, f"test_storage_{uuid.uuid4().hex}.json")
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_comprehensive_evaluation_integration(self):
        initial_capital = round(random.uniform(10000.0, 100000.0), 2)
        strategy_params = {
            "hedge_ratio": round(random.uniform(0.1, 0.9), 2),
            "stop_loss": round(random.uniform(0.01, 0.05), 3)
        }

        result = self.bridge.run_comprehensive_evaluation(
            self.symbol, 
            initial_capital, 
            strategy_params
        )

        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by the bridge.")
        
        with open(self.storage_file, "r") as f:
            storage_data = json.load(f)
        self.assertIsInstance(storage_data, dict)

        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

        eval_result = self.bridge.evaluate_strategy_backtest(
            self.symbol,
            initial_capital,
            strategy_params
        )
        self.assertIn("backtest_summary", eval_result)
        self.assertIn("performance_metrics", eval_result)
        self.assertIn("performance_evaluation", eval_result)

        perf_eval = self.bridge.evaluate_backtest_performance(self.symbol)
        self.assertIsInstance(perf_eval, dict)
        self.assertIn("performance_metrics", perf_eval)

if __name__ == "__main__":
    unittest.main()