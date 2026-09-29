import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.random_suffix}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.symbol = f"SYM_{self.random_suffix}"
        self.shifts = [random.uniform(0.01, 0.05), random.uniform(0.06, 0.10)]
        self.allocation = round(random.uniform(0.1, 0.9), 2)
        self.percentage = round(random.uniform(5.0, 25.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_optimize_and_evaluate_integration(self):
        result = self.optimizer.optimize_and_evaluate(
            symbol=self.symbol,
            allocation=self.allocation,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        weights = result["optimized_weights"]
        self.assertIn(self.symbol, weights)
        self.assertEqual(weights[self.symbol], self.allocation)

        score = result["resilience_score"]
        self.assertIsInstance(score, float)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_optimize_strategy_integration(self):
        result = self.optimizer.optimize_strategy(
            symbol=self.symbol,
            shifts=self.shifts,
            percentage=self.percentage
        )

        self.assertIsInstance(result, dict)
        self.assertIn('backtest', result)
        self.assertIn('simulation', result)

    def test_evaluate_resilience_integration(self):
        result = self.optimizer.evaluate_resilience(
            symbol=self.symbol,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertIn('stress_data', result)
        self.assertIn('drawdown_checked', result)
        self.assertIsInstance(result['drawdown_checked'], float)

    def test_get_strategy_summary_integration(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["summary"], "active")
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)

if __name__ == '__main__':
    unittest.main()