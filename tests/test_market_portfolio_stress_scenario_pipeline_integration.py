import unittest
import json
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

        initial_data = {
            self.symbol: {
                "base_value": round(random.uniform(1000.0, 50000.0), 2),
                "assets": random.randint(1, 10)
            }
        }
        with open(self.storage_file, "w") as f:
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

    def test_pipeline_with_invalid_storage(self):
        invalid_file = f"invalid_{uuid.uuid4()}.json"
        with open(invalid_file, "w") as f:
            f.write("NOT_JSON")

        try:
            result = run_stress_scenario_pipeline(invalid_file, self.symbol, self.percentage, self.shifts)
            self.assertIsInstance(result, dict)
            self.assertIn("simulation", result)
        finally:
            if os.path.exists(invalid_file):
                os.remove(invalid_file)

if __name__ == "__main__":
    unittest.main()