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

    def test_validate_allocation_boundaries_and_types(self):
        random_valid = random.uniform(0.0, 1.0)
        self.assertEqual(self.optimizer._validate_allocation(random_valid), float(random_valid))
        
        self.assertEqual(self.optimizer._validate_allocation(-5.5), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(15.5), 1.0)
        
        random_string_num = str(random.uniform(0.1, 0.9))
        self.assertEqual(self.optimizer._validate_allocation(random_string_num), float(random_string_num))
        
        invalid_input_uuid = uuid.uuid4().hex
        self.assertEqual(self.optimizer._validate_allocation(invalid_input_uuid), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(None), 0.0)

    def test_optimize_and_evaluate_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        allocation = random.uniform(0.0, 1.0)
        shift_val = random.randint(1, 30)

        result = self.optimizer.optimize_and_evaluate(symbol, allocation, shift_val)

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        self.assertEqual(result["optimized_weights"], {symbol: self.optimizer._validate_allocation(allocation)})
        self.assertIsInstance(result["resilience_score"], float)

    def test_get_strategy_summary_real_structure(self):
        symbol = f"ASSET_{uuid.uuid4().hex[:5].upper()}"
        summary = self.optimizer.get_strategy_summary(symbol)

        self.assertIsInstance(summary, dict)
        self.assertIn(symbol, summary)
        self.assertEqual(summary[symbol]["summary"], "active")
        self.assertEqual(summary[symbol]["storage"], self.storage_file)

    def test_load_strategy_stream_io(self):
        stream_file = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.bin")
        random_bytes = bytes(random.getrandbits(8) for _ in range(64))
        
        with open(stream_file, 'wb') as f:
            f.write(random_bytes)

        loaded_data = self.optimizer.load_strategy_stream(stream_file)
        self.assertEqual(loaded_data, random_bytes)

        if os.path.exists(stream_file):
            os.remove(stream_file)

if __name__ == '__main__':
    unittest.main()