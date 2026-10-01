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
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_pipeline_class_execution_real_flow(self):
        initial_data = {
            self.symbol: {
                "base_price": round(random.uniform(10.0, 1000.0), 2),
                "volume": random.randint(100, 10000)
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_test"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_report"].get("symbol"), self.symbol)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_pipeline_function_execution_resilience_corrupted_storage(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{corrupted_json_data_12345")

        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        self.assertEqual(result["simulation"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_test"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_report"].get("symbol"), self.symbol)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{}")

if __name__ == "__main__":
    unittest.main()