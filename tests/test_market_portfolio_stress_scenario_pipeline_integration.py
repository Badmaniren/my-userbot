import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2), round(random.uniform(-20.0, 20.0), 2)]
        
        initial_data = {
            self.symbol: {
                "base_price": round(random.uniform(10.0, 1000.0), 2),
                "quantity": random.randint(1, 1000)
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

    def test_run_stress_scenario_pipeline_function(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        
        sim_data = result["simulation"]
        self.assertIsInstance(sim_data, dict)

    def test_pipeline_with_nonexistent_storage(self):
        non_existent_file = f"non_existent_{uuid.uuid4()}.json"
        try:
            result = run_stress_scenario_pipeline(non_existent_file, self.symbol, self.percentage, self.shifts)
            self.assertIsInstance(result, dict)
            self.assertTrue(os.path.exists(non_existent_file))
        finally:
            if os.path.exists(non_existent_file):
                os.remove(non_existent_file)

if __name__ == "__main__":
    unittest.main()