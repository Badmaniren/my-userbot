import unittest
import tempfile
import os
import uuid
import random
from skills.market_portfolio_net_yield_evaluator import NetYieldEvaluator, evaluate_net_yield

class TestNetYieldEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_filename = f"test_portfolio_{uuid.uuid4()}.json"
        self.db_path = os.path.join(self.test_dir.name, self.db_filename)
        self.portfolio_url = f"file://{self.db_path}"
        
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("{}")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_net_yield_evaluator_composition(self):
        evaluator = NetYieldEvaluator(storage_file=self.db_path)
        
        self.assertIsNotNone(evaluator.valuation_engine)
        self.assertIsNotNone(evaluator.tax_calculator)

        result = evaluator.evaluate_net_yield(self.portfolio_url)
        
        self.assertIn("net_portfolio_value", result)
        self.assertIn("net_yield_percentage", result)
        self.assertIsInstance(result["net_portfolio_value"], (int, float))
        self.assertIsInstance(result["net_yield_percentage"], (int, float))

    def test_net_yield_evaluator_with_stream_composition(self):
        evaluator = NetYieldEvaluator(storage_file=self.db_path)
        
        random_dividend = round(random.uniform(10.0, 500.0), 2)
        stream = [{"amount": random_dividend}]
        
        result = evaluator.evaluate_net_yield_with_stream(self.portfolio_url, stream)
        
        self.assertIn("net_portfolio_value", result)
        self.assertIn("net_yield_percentage", result)

    def test_evaluate_net_yield_function_integration(self):
        portfolio_id = str(uuid.uuid4())
        
        result = evaluate_net_yield(portfolio_id, self.portfolio_url)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("net_yield", result)
        self.assertIsInstance(result["net_yield"], (int, float))

if __name__ == "__main__":
    unittest.main()