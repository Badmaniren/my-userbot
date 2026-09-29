import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        initial_data = {
            "portfolio": {
                "cash": round(random.uniform(10000.0, 50000.0), 2)
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_execution_class_and_function_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-0.1, 0.1), 4), round(random.uniform(-0.2, 0.2), 4)]

        pipeline_instance = PortfolioStressScenarioPipeline(self.storage_file)
        
        try:
            class_result = pipeline_instance.execute(symbol, percentage, shifts)
            self.assertIsInstance(class_result, dict)
            self.assertIn("simulation", class_result)
            self.assertIn("stress_test", class_result)
            self.assertIn("stress_report", class_result)
        except Exception as e:
            self.fail(f"PortfolioStressScenarioPipeline.execute raised unexpected exception: {e}")

        try:
            func_result = run_stress_scenario_pipeline(self.storage_file, symbol, percentage, shifts)
            self.assertIsInstance(func_result, dict)
            self.assertIn("simulation", func_result)
            self.assertIn("stress_test", func_result)
            self.assertIn("stress_report", func_result)

            self.assertEqual(func_result["simulation"]["symbol"], symbol)
            self.assertEqual(func_result["stress_test"]["symbol"], symbol)
            self.assertEqual(func_result["stress_report"]["symbol"], symbol)
        except Exception as e:
            self.fail(f"run_stress_scenario_pipeline raised unexpected exception: {e}")

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            file_content = json.load(f)
        self.assertIsInstance(file_content, dict)

if __name__ == "__main__":
    unittest.main()