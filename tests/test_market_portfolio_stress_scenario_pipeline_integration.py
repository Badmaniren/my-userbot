import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.json"
        self.symbol = "BTC"
        initial_data = {
            self.symbol: {
                "symbol": self.symbol,
                "price": 50000.0,
                "quantity": 2.0
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_execution_class_integration(self):
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(self.symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_run_stress_scenario_pipeline_function_integration(self):
        percentage = round(random.uniform(-30.0, 30.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2) for _ in range(2)]

        result = run_stress_scenario_pipeline(self.storage_file, self.symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, "r", encoding="utf-8") as f:
            storage_content = json.load(f)
        self.assertIsInstance(storage_content, dict)

if __name__ == "__main__":
    unittest.main()
