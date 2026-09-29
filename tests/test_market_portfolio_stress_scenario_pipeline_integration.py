import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, -5.0), 2)
        self.shifts = [round(random.uniform(-0.2, -0.01), 2) for _ in range(random.randint(1, 3))]
        
        initial_data = {
            self.symbol: {
                "base_price": round(random.uniform(10.0, 1000.0), 2),
                "volume": random.randint(100, 10000)
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_class_execution(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_pipeline_functional_execution(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        
        sim_data = result["simulation"]
        self.assertIsInstance(sim_data, dict)

    def test_pipeline_with_corrupted_storage(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("INVALID_JSON_CONTENT_" + uuid.uuid4().hex)

        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

if __name__ == "__main__":
    unittest.main()