import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + uuid.uuid4().hex
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.db")
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

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

    def test_validate_allocation_boundary_cases(self):
        rand_val = random.uniform(-10.0, 10.0)
        validated = self.optimizer._validate_allocation(rand_val)
        
        if rand_val < 0.0:
            self.assertEqual(validated, 0.0)
        elif rand_val > 1.0:
            self.assertEqual(validated, 1.0)
        else:
            self.assertEqual(validated, float(rand_val))

        invalid_val = f"invalid_weight_{uuid.uuid4().hex}"
        self.assertEqual(self.optimizer._validate_allocation(invalid_val), 0.0)

    def test_optimize_and_evaluate_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        allocation = random.uniform(0.1, 0.9)
        shifts = [random.randint(1, 30), random.randint(31, 60)]

        result = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts)

        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        self.assertEqual(result["optimized_weights"], {symbol: allocation})
        self.assertIsInstance(result["resilience_score"], float)

    def test_get_strategy_summary_real_db_integration(self):
        symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        summary = self.optimizer.get_strategy_summary(symbol)

        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["storage"], self.storage_file)
        self.assertEqual(summary[symbol]["summary"], "active")

if __name__ == '__main__':
    unittest.main()