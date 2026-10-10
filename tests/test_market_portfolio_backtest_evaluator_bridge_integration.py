import unittest
import os
import tempfile
import uuid
import random
import json
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.initial_capital = float(random.randint(10000, 100000))
        self.strategy_params = {
            "threshold": round(random.uniform(0.01, 0.05), 4),
            "window": random.randint(10, 50)
        }

    def tearDown(self):
        self.temp_dir.cleanup()

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

        with open(self.storage_file, "r") as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict)

    def test_evaluate_backtest_performance_existing_storage(self):
        with open(self.storage_file, "w") as f:
            json.dump({self.symbol: {"prefilled": random.random()}}, f)

        result = self.bridge.evaluate_backtest_performance(self.symbol)

        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

if __name__ == "__main__":
    unittest.main()