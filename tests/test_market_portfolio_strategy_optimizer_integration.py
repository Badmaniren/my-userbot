import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.db")
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

    def test_integration_optimize_and_evaluate_flow(self):
        random_allocation = round(random.uniform(0.1, 0.9), 2)
        random_shifts = [random.randint(1, 30), random.randint(31, 60)]
        
        result = self.optimizer.optimize_and_evaluate(
            symbol=self.symbol,
            allocation=random_allocation,
            shifts=random_shifts
        )

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        weights = result["optimized_weights"]
        self.assertIn(self.symbol, weights)
        self.assertEqual(weights[self.symbol], random_allocation)
        self.assertIsInstance(result["resilience_score"], float)

    def test_integration_strategy_summary_and_validation(self):
        invalid_allocations = [-5.0, 10.0, "invalid_str"]
        for bad_alloc in invalid_allocations:
            validated = self.optimizer._validate_allocation(bad_alloc)
            self.assertIn(validated, [0.0, 1.0])

        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)
        self.assertEqual(summary[self.symbol]["summary"], "active")

    def test_integration_evaluate_resilience_and_optimization(self):
        shifts_val = random.randint(5, 50)
        eval_result = self.optimizer.evaluate_resilience(self.symbol, shifts_val)
        
        self.assertIsInstance(eval_result, dict)
        self.assertIn("stress_data", eval_result)
        self.assertIn("drawdown_checked", eval_result)

        percentage_val = round(random.uniform(0.01, 0.5), 4)
        opt_result = self.optimizer.optimize_strategy(self.symbol, shifts_val, percentage_val)
        
        self.assertIsInstance(opt_result, dict)
        self.assertIn("backtest", opt_result)
        self.assertIn("simulation", opt_result)

if __name__ == "__main__":
    unittest.main()