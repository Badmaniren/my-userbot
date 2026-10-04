import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_filename = f"test_portfolio_storage_{uuid.uuid4().hex}.json"
        self.storage_file = os.path.join(self.test_dir, self.storage_filename)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_class_integration(self):
        random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        random_percentage = round(random.uniform(-50.0, 50.0), 2)
        random_shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(1, 3))]

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(random_symbol, random_percentage, random_shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"].get("symbol"), random_symbol)
        self.assertEqual(result["stress_test"].get("symbol"), random_symbol)
        self.assertEqual(result["stress_report"].get("symbol"), random_symbol)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            self.assertIsInstance(data, dict)

    def test_pipeline_function_integration(self):
        random_symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_percentage = round(random.uniform(-25.0, 25.0), 2)
        random_shifts = [round(random.uniform(-0.05, 0.05), 4) for _ in range(random.randint(1, 3))]

        result = run_stress_scenario_pipeline(self.storage_file, random_symbol, random_percentage, random_shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"].get("symbol"), random_symbol)
        self.assertEqual(result["stress_test"].get("symbol"), random_symbol)
        self.assertEqual(result["stress_report"].get("symbol"), random_symbol)

        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()