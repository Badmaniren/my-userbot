import unittest
import os
import tempfile
import uuid
import random
import json

from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.json', dir=self.test_dir.name)
        os.close(self.db_fd)
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.initial_price = round(random.uniform(100.0, 500.0), 2)
        
        dummy_data = {
            self.symbol: [
                {"price": self.initial_price, "timestamp": "2023-01-01T00:00:00"},
                {"price": round(self.initial_price * 1.05, 2), "timestamp": "2023-01-02T00:00:00"},
                {"price": round(self.initial_price * 0.98, 2), "timestamp": "2023-01-03T00:00:00"},
                {"price": round(self.initial_price * 1.10, 2), "timestamp": "2023-01-04T00:00:00"}
            ]
        }
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(dummy_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_optimizer_composition_integration(self):
        optimizer = PortfolioStrategyOptimizer(self.db_path)
        
        self.assertTrue(
            hasattr(optimizer, 'backtester') or hasattr(optimizer, 'simulator'),
            "Optimizer must compose backtester or scenario simulator modules"
        )
        
        shift_val = round(random.uniform(-0.1, 0.1), 3)
        allocation_param = round(random.uniform(0.5, 1.0), 2)
        
        optimization_result = optimizer.optimize_and_evaluate(
            symbol=self.symbol,
            allocation=allocation_param,
            shifts=shift_val
        )
        
        self.assertIsInstance(optimization_result, dict, "Optimization result must be a dictionary")
        self.assertIn("optimized_weights", optimization_result)
        self.assertIn("resilience_score", optimization_result)
        
        summary = optimizer.get_strategy_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertIn(self.symbol, summary or optimization_result)

if __name__ == '__main__':
    unittest.main()