import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.random_suffix}.db"
        self.stream_file = f"test_strategy_stream_{self.random_suffix}.bin"
        
        with open(self.storage_file, "w") as f:
            f.write("initialize_storage")
            
        with open(self.stream_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03_stream_data_" + self.random_suffix.encode())

        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def tearDown(self):
        for filepath in [self.storage_file, self.stream_file]:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    def test_integration_workflow(self):
        test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        random_allocation = round(random.uniform(-0.5, 1.5), 4)
        random_shift = round(random.uniform(1.0, 30.0), 2)
        random_percentage = round(random.uniform(0.01, 0.99), 4)

        validated_alloc = self.optimizer._validate_allocation(random_allocation)
        expected_alloc = 0.0 if random_allocation < 0.0 else (1.0 if random_allocation > 1.0 else float(random_allocation))
        self.assertEqual(validated_alloc, expected_alloc)

        summary = self.optimizer.get_strategy_summary(test_symbol)
        self.assertIn(test_symbol, summary)
        self.assertEqual(summary[test_symbol]["storage"], self.storage_file)
        self.assertEqual(summary[test_symbol]["summary"], "active")

        opt_result = self.optimizer.optimize_strategy(test_symbol, random_shift, random_percentage)
        self.assertIsInstance(opt_result, dict)
        self.assertIn('backtest', opt_result)
        self.assertIn('simulation', opt_result)

        resilience = self.optimizer.evaluate_resilience(test_symbol, [random_shift, random_shift * 1.5])
        self.assertIsInstance(resilience, dict)
        self.assertIn('stress_data', resilience)
        self.assertIn('drawdown_checked', resilience)
        self.assertIsInstance(resilience['drawdown_checked'], float)

        stream_data = self.optimizer.load_strategy_stream(self.stream_file)
        self.assertIn(self.random_suffix.encode(), stream_data)

        combined_result = self.optimizer.optimize_and_evaluate(test_symbol, random_allocation, [random_shift])
        self.assertIsInstance(combined_result, dict)
        self.assertIn("optimized_weights", combined_result)
        self.assertIn("resilience_score", combined_result)
        self.assertIn("backtest", combined_result)
        self.assertIn("stress", combined_result)

        self.assertEqual(combined_result["optimized_weights"][test_symbol], expected_alloc)
        self.assertTrue(0.0 <= combined_result["resilience_score"] <= 1.0)

if __name__ == "__main__":
    unittest.main()