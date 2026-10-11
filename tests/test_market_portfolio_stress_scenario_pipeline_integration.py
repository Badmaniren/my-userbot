import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2), round(random.uniform(-10.0, 10.0), 2)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_class_execution(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        
        self.assertEqual(result["simulation"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_test"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_report"].get("symbol"), self.symbol)

    def test_pipeline_functional_execution(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertTrue(os.path.exists(self.storage_file))
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_test"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_report"].get("symbol"), self.symbol)

if __name__ == "__main__":
    unittest.main()