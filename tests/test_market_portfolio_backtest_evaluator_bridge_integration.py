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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_storage_creation_and_comprehensive_evaluation(self):
        initial_capital = round(random.uniform(10000.0, 100000.0), 2)
        strategy_params = {
            "sma_period": random.randint(10, 50),
            "risk_tolerance": round(random.uniform(0.01, 0.05), 4)
        }

        result = self.bridge.run_comprehensive_evaluation(self.symbol, initial_capital, strategy_params)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by the bridge.")
        
        with open(self.storage_file, "r") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict, "Storage content must be a dictionary JSON object.")

        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_evaluate_strategy_backtest_flow(self):
        initial_capital = round(random.uniform(5000.0, 50000.0), 2)
        strategy_params = {
            "leverage": round(random.uniform(1.0, 3.0), 2),
            "threshold": round(random.uniform(0.001, 0.01), 4)
        }

        result = self.bridge.evaluate_strategy_backtest(self.symbol, initial_capital, strategy_params)

        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_evaluate_backtest_performance_existing_storage(self):
        with open(self.storage_file, "w") as f:
            json.dump({self.symbol: {"initialized": True, "id": str(uuid.uuid4())}}, f)

        result = self.bridge.evaluate_backtest_performance(self.symbol)

        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

if __name__ == "__main__":
    unittest.main()