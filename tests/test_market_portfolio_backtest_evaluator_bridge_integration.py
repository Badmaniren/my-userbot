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
        self.initial_capital = float(random.randint(10000, 100000))
        self.strategy_params = {
            "sma_window": random.randint(10, 50),
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
        self.assertGreater(os.path.getsize(self.storage_file), 0)

        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_evaluate_strategy_backtest_flow(self):
        result = self.bridge.evaluate_strategy_backtest(
            self.symbol,
            self.initial_capital,
            self.strategy_params
        )

        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

    def test_evaluate_backtest_performance_existing_storage(self):
        with open(self.storage_file, "w") as f:
            json.dump({self.symbol: {"initialized": True, "id": uuid.uuid4().str}}, f)

        result = self.bridge.evaluate_backtest_performance(self.symbol)

        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

if __name__ == "__main__":
    unittest.main()