import unittest
import os
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data_integration"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"test_storage_{uuid.uuid4().hex}.db")
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.shifts = [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)]
        self.percentage = random.uniform(5.0, 25.0)
        self.allocation = random.uniform(0.1, 1.0)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_optimize_strategy_real_execution(self):
        result = self.optimizer.optimize_strategy(self.symbol, self.shifts, self.percentage)
        self.assertIsInstance(result, dict)
        self.assertIn('backtest', result)
        self.assertIn('simulation', result)

    def test_evaluate_resilience_real_execution(self):
        result = self.optimizer.evaluate_resilience(self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn('stress_data', result)
        self.assertIn('drawdown_checked', result)

    def test_optimize_and_evaluate_real_execution(self):
        result = self.optimizer.optimize_and_evaluate(self.symbol, self.allocation, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["optimized_weights"][self.symbol], self.allocation)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

    def test_get_strategy_summary_real_execution(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)

    def test_load_strategy_stream_real_file(self):
        stream_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.bin")
        random_bytes = os.urandom(64)
        with open(stream_path, 'wb') as f:
            f.write(random_bytes)
        
        try:
            content = self.optimizer.load_strategy_stream(stream_path)
            self.assertEqual(content, random_bytes)
        finally:
            if os.path.exists(stream_path):
                os.remove(stream_path)

if __name__ == '__main__':
    unittest.main()