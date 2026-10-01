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
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.initial_capital = float(random.randint(10000, 1000000))
        self.strategy_params = {
            "sma_period": random.randint(10, 50),
            "risk_tolerance": round(random.uniform(0.01, 0.05), 4)
        }

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_storage_creation_and_comprehensive_evaluation(self):
        self.assertFalse(os.path.exists(self.storage_file))
        
        result = self.bridge.run_comprehensive_evaluation(
            self.symbol, 
            self.initial_capital, 
            self.strategy_params
        )

        self.assertTrue(os.path.exists(self.storage_file))
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_evaluate_strategy_backtest(self):
        result = self.bridge.evaluate_strategy_backtest(
            self.symbol, 
            self.initial_capital, 
            self.strategy_params
        )

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

    def test_evaluate_backtest_performance(self):
        self.bridge.run_comprehensive_evaluation(
            self.symbol, 
            self.initial_capital, 
            self.strategy_params
        )

        evaluation_result = self.bridge.evaluate_backtest_performance(self.symbol)

        self.assertIsInstance(evaluation_result, dict)
        self.assertIn("backtest_summary", evaluation_result)
        self.assertIn("performance_metrics", evaluation_result)
        self.assertIn("performance_evaluation", evaluation_result)

if __name__ == "__main__":
    unittest.main()