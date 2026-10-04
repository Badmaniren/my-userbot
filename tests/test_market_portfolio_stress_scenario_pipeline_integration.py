import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_class_execution_integration(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file should be created by the pipeline.")
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            file_content = f.read()
        storage_data = json.loads(file_content)
        self.assertIsInstance(storage_data, dict, "Storage content must be a dictionary.")

        self.assertIsInstance(result, dict, "Pipeline execution result must be a dictionary.")
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"]["symbol"], self.symbol)
        self.assertEqual(result["simulation"]["percentage"], self.percentage)
        self.assertEqual(result["stress_test"]["symbol"], self.symbol)
        self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_pipeline_functional_execution_integration(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file should be created by the functional pipeline.")
        
        self.assertIsInstance(result, dict, "Functional pipeline result must be a dictionary.")
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"]["symbol"], self.symbol)
        self.assertEqual(result["simulation"]["percentage"], self.percentage)
        self.assertEqual(result["stress_test"]["symbol"], self.symbol)
        self.assertEqual(result["stress_report"]["symbol"], self.symbol)

if __name__ == "__main__":
    unittest.main()