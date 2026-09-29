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
        self.symbol = f"SYM_{random.randint(1000, 9999)}"

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

    def test_integration_optimize_and_evaluate_pipeline(self):
        allocation = round(random.uniform(0.1, 0.9), 2)
        shift_value = round(random.uniform(0.01, 0.05), 4)

        result = self.optimizer.optimize_and_evaluate(self.symbol, allocation, shift_value)

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        self.assertEqual(result["optimized_weights"], {self.symbol: allocation})
        self.assertIsInstance(result["resilience_score"], float)

    def test_integration_evaluate_resilience_boundaries(self):
        invalid_allocation = "invalid_alloc_" + uuid.uuid4().hex[:6]
        validated = self.optimizer._validate_allocation(invalid_allocation)
        self.assertEqual(validated, 0.0)

        high_allocation = random.uniform(1.5, 10.0)
        validated_high = self.optimizer._validate_allocation(high_allocation)
        self.assertEqual(validated_high, 1.0)

        shifts = [round(random.uniform(0.01, 0.1), 4) for _ in range(3)]
        resilience_data = self.optimizer.evaluate_resilience(self.symbol, shifts)

        self.assertIsInstance(resilience_data, dict)
        self.assertIn("stress_data", resilience_data)
        self.assertIn("drawdown_checked", resilience_data)

    def test_integration_strategy_summary_and_stream(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)

        dummy_filepath = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.bin")
        test_content = uuid.uuid4().bytes
        with open(dummy_filepath, "wb") as f:
            f.write(test_content)

        stream_data = self.optimizer.load_strategy_stream(dummy_filepath)
        self.assertEqual(stream_data, test_content)

if __name__ == "__main__":
    unittest.main()