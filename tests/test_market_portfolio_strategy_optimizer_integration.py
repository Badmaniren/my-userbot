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
        self.symbol = f"SYM_{random.randint(100, 999)}"
        
    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_optimize_and_evaluate_workflow(self):
        random_allocation = round(random.uniform(-0.5, 1.5), 2)
        random_shift = random.randint(1, 30)
        
        result = self.optimizer.optimize_and_evaluate(
            symbol=self.symbol, 
            allocation=random_allocation, 
            shifts=random_shift
        )
        
        self.assertIsInstance(result, dict, "Результат должен быть словарем")
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)
        
        expected_allocation = max(0.0, min(1.0, float(random_allocation)))
        self.assertEqual(result["optimized_weights"][self.symbol], expected_allocation)
        self.assertIsInstance(result["resilience_score"], float)

    def test_integration_strategy_summary(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)
        self.assertEqual(summary[self.symbol]["summary"], "active")

    def test_integration_load_strategy_stream_boundary(self):
        temp_file = f"temp_stream_{self.random_suffix}.bin"
        random_payload = uuid.uuid4().bytes
        with open(temp_file, 'wb') as f:
            f.write(random_payload)
            
        try:
            stream_data = self.optimizer.load_strategy_stream(temp_file)
            self.assertEqual(stream_data, random_payload)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    unittest.main()