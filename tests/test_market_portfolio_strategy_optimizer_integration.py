import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.allocation = round(random.uniform(0.1, 1.0), 4)
        self.shifts = [random.randint(1, 10), random.randint(11, 30)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_optimize_and_evaluate_integration(self):
        result = self.optimizer.optimize_and_evaluate(self.symbol, self.allocation, self.shifts)
        
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

    def test_get_strategy_summary_integration(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)
        self.assertEqual(summary[self.symbol]["summary"], "active")

    def test_optimize_strategy_boundary_conditions(self):
        percentage = round(random.uniform(-0.5, 1.5), 2)
        result = self.optimizer.optimize_strategy(self.symbol, self.shifts, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertIn('backtest', result)
        self.assertIn('simulation', result)

    def test_evaluate_resilience_integration(self):
        result = self.optimizer.evaluate_resilience(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn('stress_data', result)
        self.assertIn('drawdown_checked', result)
        self.assertIsInstance(result['drawdown_checked'], float)

if __name__ == '__main__':
    unittest.main()