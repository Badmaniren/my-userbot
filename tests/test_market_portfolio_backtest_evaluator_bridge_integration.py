import unittest
import os
import tempfile
import json
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        self.strategy_params = {
            "sma_short": random.randint(5, 20),
            "sma_long": random.randint(21, 100),
            "risk_tolerance": round(random.uniform(0.01, 0.05), 4)
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_storage_creation_and_comprehensive_evaluation_integration(self):
        self.assertFalse(os.path.exists(self.storage_file), "Storage file should not exist before evaluation execution.")
        
        result = self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=self.initial_capital,
            strategy_params=self.strategy_params
        )

        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be dynamically created by the bridge.")
        self.assertGreater(os.path.getsize(self.storage_file), 0, "Storage file must contain serialized data structures.")

        self.assertIsInstance(result, dict)
        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def evaluate_strategy_and_performance_pipeline(self):
        evaluation_result = self.bridge.evaluate_strategy_backtest(
            symbol=self.symbol,
            initial_capital=self.initial_capital,
            strategy_params=self.strategy_params
        )

        self.assertIsInstance(evaluation_result, dict)
        self.assertIn("backtest_summary", evaluation_result)
        self.assertIn("performance_metrics", evaluation_result)
        self.assertIn("performance_evaluation", evaluation_result)

        stored_data_raw = self.bridge.evaluate_backtest_performance(self.symbol)
        self.assertIsInstance(stored_data_raw, dict)
        self.assertIn("backtest_summary", stored_data_raw)
        self.assertIn("performance_metrics", stored_data_raw)
        self.assertIn("performance_evaluation", stored_data_raw)

if __name__ == "__main__":
    unittest.main()