import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_filename = f"test_portfolio_storage_{uuid.uuid4()}.db"
        self.storage_path = os.path.join(self.test_dir, self.storage_filename)
        
        with open(self.storage_path, "w") as f:
            f.write("INITIAL_DB_STATE")

        self.optimizer = PortfolioStrategyOptimizer(self.storage_path)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

    def test_integration_optimize_and_evaluate_real_data(self):
        allocation = round(random.uniform(0.0, 1.0), 4)
        shifts = [random.randint(1, 30), random.randint(31, 60)]

        result = self.optimizer.optimize_and_evaluate(self.symbol, allocation, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        self.assertEqual(result["optimized_weights"], {self.symbol: allocation})
        self.assertIsInstance(result["resilience_score"], float)
        self.assertTrue(0.0 <= result["resilience_score"] <= 1.0)

    def test_integration_evaluate_resilience_flow(self):
        shifts = random.randint(5, 50)
        
        evaluation = self.optimizer.evaluate_resilience(self.symbol, shifts)

        self.assertIsInstance(evaluation, dict)
        self.assertIn("stress_data", evaluation)
        self.assertIn("drawdown_checked", evaluation)
        self.assertIsInstance(evaluation["drawdown_checked"], float)

    def test_integration_strategy_summary_storage_link(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)

        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_path)
        self.assertEqual(summary[self.symbol]["summary"], "active")

    def test_integration_load_strategy_stream(self):
        stream_data = self.optimizer.load_strategy_stream(self.storage_path)
        self.assertIsInstance(stream_data, bytes)
        self.assertEqual(stream_data, b"INITIAL_DB_STATE")

if __name__ == '__main__':
    unittest.main()