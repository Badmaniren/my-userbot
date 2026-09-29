import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_storage_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_storage_{uuid.uuid4().hex}.json")
        
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

        initial_data = {
            self.symbol: {
                "shares": random.randint(10, 1000),
                "purchase_price": round(random.uniform(10.0, 500.0), 2)
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_pipeline_class_execution(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertNotEqual(result["simulation"], {})
        self.assertNotEqual(result["stress_test"], {})

    def test_pipeline_functional_execution(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        sim_res = result["simulation"]
        self.assertIsInstance(sim_res, dict)
        
        stress_res = result["stress_test"]
        self.assertIsInstance(stress_res, dict)

    def test_pipeline_with_corrupted_storage(self):
        corrupted_file = os.path.join(self.test_dir, f"corrupted_{uuid.uuid4().hex}.json")
        with open(corrupted_file, "w", encoding="utf-8") as f:
            f.write("INVALID_JSON_CONTENT_")

        try:
            result = run_stress_scenario_pipeline(corrupted_file, self.symbol, self.percentage, self.shifts)
            self.assertIsInstance(result, dict)
            self.assertIn("simulation", result)
            
            self.assertTrue(os.path.exists(corrupted_file))
            with open(corrupted_file, "r", encoding="utf-8") as f:
                fixed_content = json.load(f)
            self.assertEqual(fixed_content, {})
        finally:
            if os.path.exists(corrupted_file):
                os.remove(corrupted_file)

if __name__ == "__main__":
    unittest.main()