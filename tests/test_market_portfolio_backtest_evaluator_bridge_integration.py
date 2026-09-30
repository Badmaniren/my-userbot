import unittest
import os
import uuid
import random
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge

class TestMarketPortfolioBacktestEvaluatorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.random_suffix}.db"
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.initial_capital = round(random.uniform(10000.0, 100000.0), 2)
        self.strategy_params = {
            "slippage_tolerance": round(random.uniform(0.001, 0.05), 4),
            "execution_delay_seconds": random.randint(1, 10),
            "max_position_size": round(random.uniform(100.0, 5000.0), 2)
        }
        self.bridge = MarketPortfolioBacktestEvaluatorBridge(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_comprehensive_evaluation_and_storage_creation(self):
        self.assertFalse(
            os.path.exists(self.storage_file),
            "Storage file should not exist prior to running backtest execution."
        )

        result = self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=self.initial_capital,
            strategy_params=self.strategy_params
        )

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Integration failure: Storage file must be created by the underlying skills during execution."
        )

        self.assertIsInstance(result, dict, "Result of comprehensive evaluation must be a dictionary.")
        self.assertIn("backtest_execution", result)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("evaluation", result)

    def test_strategy_backtest_evaluation_flow(self):
        evaluation_result = self.bridge.evaluate_strategy_backtest(
            symbol=self.symbol,
            initial_capital=self.initial_capital,
            strategy_params=self.strategy_params
        )

        self.assertIsInstance(evaluation_result, dict, "Strategy backtest evaluation must return a dictionary.")
        self.assertIn("backtest_summary", evaluation_result)
        self.assertIn("performance_metrics", evaluation_result)
        self.assertIn("performance_evaluation", evaluation_result)

        summary = evaluation_result["backtest_summary"]
        self.assertIsNotNone(summary, "Backtest summary should not be None after execution.")

    def test_evaluate_backtest_performance_existing_storage(self):
        self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=self.initial_capital,
            strategy_params=self.strategy_params
        )

        performance_result = self.bridge.evaluate_backtest_performance(self.symbol)

        self.assertIsInstance(performance_result, dict, "Performance evaluation must return a dictionary.")
        self.assertIn("backtest_summary", performance_result)
        self.assertIn("performance_metrics", performance_result)
        self.assertIn("performance_evaluation", performance_result)

if __name__ == "__main__":
    unittest.main()