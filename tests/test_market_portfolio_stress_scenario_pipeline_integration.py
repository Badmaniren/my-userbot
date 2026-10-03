import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        initial_data = {
            self.symbol: {
                "base_price": round(random.uniform(10.0, 1000.0), 2),
                "shares": random.randint(10, 500)
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_pipeline_class_execution(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"]["symbol"], self.symbol)
        self.assertEqual(result["stress_test"]["symbol"], self.symbol)
        self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_pipeline_functional_execution(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"]["symbol"], self.symbol)
        self.assertEqual(result["stress_test"]["symbol"], self.symbol)
        self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_pipeline_with_nonexistent_storage(self):
        non_existent_file = os.path.join(self.test_dir, f"missing_{uuid.uuid4().hex}.json")
        pipeline = PortfolioStressScenarioPipeline(non_existent_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertTrue(os.path.exists(non_existent_file))

        if os.path.exists(non_existent_file):
            os.remove(non_existent_file)

if __name__ == "__main__":
    unittest.main()