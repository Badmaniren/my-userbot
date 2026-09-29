import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4()}.db")
        
        with open(self.storage_file, "w") as f:
            f.write("INITIAL_DB_STATE_" + str(uuid.uuid4()))
            
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.symbol = "SYM_" + uuid.uuid4().hex[:6].upper()
        self.random_allocation = round(random.uniform(0.0, 1.0), 4)
        self.random_shift = round(random.uniform(-0.5, 0.5), 4)
        self.random_percentage = round(random.uniform(1.0, 20.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_optimize_and_evaluate_pipeline(self):
        result = self.optimizer.optimize_and_evaluate(
            self.symbol, 
            self.random_allocation, 
            self.random_shift
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)
        
        weights = result["optimized_weights"]
        self.assertIn(self.symbol, weights)
        self.assertEqual(weights[self.symbol], self.random_allocation)
        
        score = result["resilience_score"]
        self.assertIsInstance(score, float)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_integration_strategy_summary_and_validation(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)
        
        validated = self.optimizer._validate_allocation(self.random_allocation + 1.5)
        self.assertEqual(validated, 1.0)

        negative_validated = self.optimizer._validate_allocation(-5.0)
        self.assertEqual(negative_validated, 0.0)

    def test_integration_evaluate_resilience_and_stream(self):
        resilience = self.optimizer.evaluate_resilience(self.symbol, self.random_shift)
        self.assertIsInstance(resilience, dict)
        self.assertIn("stress_data", resilience)
        self.assertIn("drawdown_checked", resilience)
        
        stream_data = self.optimizer.load_strategy_stream(self.storage_file)
        self.assertIsInstance(stream_data, bytes)
        self.assertTrue(len(stream_data) > 0)

if __name__ == "__main__":
    unittest.main()