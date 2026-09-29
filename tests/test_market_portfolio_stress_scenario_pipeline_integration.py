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
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]
        
        initial_data = {
            self.symbol: {
                "base_value": round(random.uniform(100.0, 1000.0), 2),
                "liquidity_factor": round(random.uniform(0.5, 1.0), 2)
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
        
        self.assertEqual(result["simulation"].get("symbol"), self.symbol)
        self.assertEqual(result["simulation"].get("percentage"), self.percentage)
        self.assertEqual(result["stress_test"].get("symbol"), self.symbol)
        self.assertEqual(result["stress_test"].get("shifts"), self.shifts)

    def test_pipeline_invalid_storage_recovery(self):
        invalid_file = f"invalid_{uuid.uuid4()}.json"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("corrupted_data_not_json")

        try:
            result = run_stress_scenario_pipeline(invalid_file, self.symbol, self.percentage, self.shifts)
            self.assertIsInstance(result, dict)
            self.assertIn("simulation", result)
            self.assertTrue(os.path.exists(invalid_file))
            with open(invalid_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "{}")
        finally:
            if os.path.exists(invalid_file):
                os.remove(invalid_file)

if __name__ == "__main__":
    unittest.main()