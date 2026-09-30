import unittest
import json
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

        initial_data = {
            self.symbol: {
                "base_value": round(random.uniform(100.0, 10000.0), 2),
                "shares": random.randint(10, 500)
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

    def test_pipeline_functional_execution_strict_exceptions(self):
        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

    def test_pipeline_with_corrupted_storage_strict(self):
        corrupted_file = f"corrupted_{uuid.uuid4().hex}.json"
        with open(corrupted_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json")

        try:
            with self.assertRaises((json.JSONDecodeError, ValueError, Exception)):
                run_stress_scenario_pipeline(corrupted_file, self.symbol, self.percentage, self.shifts)
        finally:
            if os.path.exists(corrupted_file):
                os.remove(corrupted_file)

if __name__ == "__main__":
    unittest.main()