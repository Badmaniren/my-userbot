import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_file = os.path.join(self.test_dir, f"test_portfolio_storage_{uuid.uuid4()}.db")
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_optimize_and_evaluate(self):
        random_allocation = round(random.uniform(0.1, 0.9), 2)
        random_shift = round(random.uniform(1.0, 5.0), 2)

        result = self.optimizer.optimize_and_evaluate(
            symbol=self.test_symbol,
            allocation=random_allocation,
            shifts=random_shift
        )

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        self.assertIn(self.test_symbol, result["optimized_weights"])
        self.assertEqual(result["optimized_weights"][self.test_symbol], random_allocation)
        self.assertIsInstance(result["resilience_score"], float)

    def test_integration_strategy_summary(self):
        summary = self.optimizer.get_strategy_summary(self.test_symbol)
        
        self.assertIsInstance(summary, dict)
        self.assertIn(self.test_symbol, summary)
        self.assertEqual(summary[self.test_symbol]["summary"], "active")
        self.assertEqual(summary[self.test_symbol]["storage"], self.storage_file)

    def test_integration_load_strategy_stream_lifecycle(self):
        dummy_content = uuid.uuid4().bytes
        temp_stream_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4()}.bin")
        
        with open(temp_stream_path, 'wb') as f:
            f.write(dummy_content)

        try:
            read_bytes = self.optimizer.load_strategy_stream(temp_stream_path)
            self.assertEqual(read_bytes, dummy_content)
        finally:
            if os.path.exists(temp_stream_path):
                os.remove(temp_stream_path)

if __name__ == '__main__':
    unittest.main()