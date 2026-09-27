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
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.allocation = round(random.uniform(0.1, 1.0), 4)
        self.shifts = [random.randint(1, 10), random.randint(11, 30)]
        self.percentage = round(random.uniform(1.0, 15.0), 2)

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

    def test_optimize_and_evaluate_integration(self):
        result = self.optimizer.optimize_and_evaluate(self.symbol, self.allocation, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("optimized_weights", result)
        self.assertIn("resilience_score", result)
        self.assertIn("backtest", result)
        self.assertIn("stress", result)

        self.assertEqual(result["optimized_weights"], {self.symbol: self.allocation})
        self.assertIsInstance(result["resilience_score"], float)

    def test_optimize_strategy_integration(self):
        result = self.optimizer.optimize_strategy(self.symbol, self.shifts, self.percentage)

        self.assertIsInstance(result, dict)
        self.assertIn('backtest', result)
        self.assertIn('simulation', result)

    def test_evaluate_resilience_integration(self):
        result = self.optimizer.evaluate_resilience(self.symbol, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn('stress_data', result)
        self.assertIn('drawdown_checked', result)
        self.assertIsInstance(result['drawdown_checked'], float)

    def test_get_strategy_summary_integration(self):
        summary = self.optimizer.get_strategy_summary(self.symbol)

        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary)
        self.assertEqual(summary[self.symbol]["storage"], self.storage_file)
        self.assertEqual(summary[self.symbol]["summary"], "active")

    def test_load_strategy_stream_integration(self):
        temp_stream_file = os.path.join(self.test_dir, f"stream_{uuid.uuid4()}.bin")
        random_bytes = bytes(random.getrandbits(8) for _ in range(64))

        with open(temp_stream_file, "wb") as f:
            f.write(random_bytes)

        loaded_data = self.optimizer.load_strategy_stream(temp_stream_file)
        self.assertEqual(loaded_data, random_bytes)
        
        if os.path.exists(temp_stream_file):
            os.remove(temp_stream_file)

if __name__ == '__main__':
    unittest.main()