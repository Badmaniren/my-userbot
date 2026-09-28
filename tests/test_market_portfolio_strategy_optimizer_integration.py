import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"test_portfolio_{uuid.uuid4()}.db")
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_integration_optimize_and_evaluate(self):
        allocation = round(random.uniform(0.1, 0.9), 2)
        shift_val = random.randint(1, 10)
        
        result = self.optimizer.optimize_and_evaluate(self.symbol, allocation, shift_val)
        
        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)
        
        weights = result["optimized_weights"]
        self.assertIn(self.symbol, weights)
        self.assertAlmostEqual(weights[self.symbol], allocation)
        self.assertIsInstance(result["resilience_score"], float)

    def test_integration_optimize_strategy_with_random_data(self):
        shifts = [random.randint(1, 5), random.randint(6, 10)]
        percentage = round(random.uniform(0.01, 0.5), 4)

        result = self.optimizer.optimize_strategy(self.symbol, shifts, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertIn('backtest', result)
        self.assertIn('simulation', result)

    def formula_validation_boundary_conditions(self):
        invalid_allocations = [-0.5, 1.5, "invalid", None]
        for alloc in invalid_allocations:
            validated = self.optimizer._validate_allocation(alloc)
            self.assertGreaterEqual(validated, 0.0)
            self.assertLessEqual(validated, 1.0)

    def test_integration_strategy_summary(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["summary"], "active")
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)

if __name__ == "__main__":
    unittest.main()