import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"db_{uuid.uuid4().hex}.db")
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

    def test_validate_allocation_edge_cases(self):
        valid_inputs = [random.uniform(-10.0, 0.0), random.uniform(0.0, 1.0), random.uniform(1.0, 10.0)]
        for val in valid_inputs:
            result = self.optimizer._validate_allocation(val)
            self.assertIsInstance(result, float)
            self.assertTrue(0.0 <= result <= 1.0)

        invalid_input = f"str_{uuid.uuid4().hex}"
        fallback_result = self.optimizer._validate_allocation(invalid_input)
        self.assertEqual(fallback_result, 0.0)

    def test_optimize_and_evaluate_integration(self):
        allocation = round(random.uniform(0.1, 0.9), 2)
        shift_val = round(random.uniform(1.0, 5.0), 2)
        
        result = self.optimizer.optimize_and_evaluate(self.symbol, allocation, shift_val)
        
        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)
        
        self.assertEqual(result["optimized_weights"], {self.symbol: allocation})
        self.assertIsInstance(result["resilience_score"], float)

    def test_evaluate_resilience_integration(self):
        shifts = [round(random.uniform(0.5, 3.0), 2) for _ in range(3)]
        
        resilience_data = self.optimizer.evaluate_resilience(self.symbol, shifts)
        
        self.assertIsInstance(resilience_data, dict)
        self.assertIn("stress_data", resilience_data)
        self.assertIn("drawdown_checked", resilience_data)
        self.assertIsInstance(resilience_data["drawdown_checked"], float)

    def test_optimize_strategy_integration(self):
        percentage = round(random.uniform(5.0, 50.0), 2)
        shift_val = round(random.uniform(1.0, 10.0), 2)
        
        opt_result = self.optimizer.optimize_strategy(self.symbol, shift_val, percentage)
        
        self.assertIsInstance(opt_result, dict)
        self.assertIn("backtest", opt_result)
        self.assertIn("simulation", opt_result)

    def test_load_strategy_stream_integration(self):
        dummy_file = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.bin")
        random_bytes = os.urandom(32)
        
        with open(dummy_file, 'wb') as f:
            f.write(random_bytes)
            
        stream_data = self.optimizer.load_strategy_stream(dummy_file)
        self.assertEqual(stream_data, random_bytes)
        
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

    def test_get_strategy_summary_integration(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["summary"], "active")
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)

if __name__ == '__main__':
    unittest.main()