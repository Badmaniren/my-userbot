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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_comprehensive_evaluation_integration(self):
        initial_capital = round(random.uniform(1000.0, 100000.0), 2)
        strategy_params = {
            "risk_tolerance": round(random.uniform(0.01, 0.1), 4),
            "lookback_period": random.randint(10, 250),
            "execution_id": uuid.uuid4().hex
        }

        result = self.bridge.run_comprehensive_evaluation(
            symbol=self.symbol,
            initial_capital_or_shifts=initial_capital,
            strategy_params=strategy_params
        )

        self.assertIsInstance(result, dict)
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
            "threshold": round(random.uniform(0.5, 5.0), 2),
            "run_id": uuid.uuid4().hex
        }

        result = self.bridge.evaluate_strategy_backtest(
            symbol=self.symbol,
            initial_capital=initial_capital,
            strategy_params=strategy_params
        )

        self.assertIsInstance(result, dict)
        self.assertIn("backtest_summary", result)
        self.assertIn("performance_metrics", result)
        self.assertIn("performance_evaluation", result)

        eval_result = self.bridge.evaluate_backtest_performance(symbol=self.symbol)
        self.assertIsInstance(eval_result, dict)
        self.assertIn("backtest_summary", eval_result)
        self.assertIn("performance_metrics", eval_result)
        self.assertIn("performance_evaluation", eval_result)

if __name__ == "__main__":
    unittest.main()