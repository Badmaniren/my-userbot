import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import run_stress_scenario_pipeline, PortfolioStressScenarioPipeline

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        initial_data = {
            str(uuid.uuid4()): {
                "balance": round(random.uniform(1000.0, 50000.0), 2),
                "assets": {
                    "AAPL": {"quantity": random.randint(1, 100), "price": round(random.uniform(100.0, 200.0), 2)}
                }
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_execution_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, -1.0), 2), round(random.uniform(1.0, 10.0), 2)]

        result = run_stress_scenario_pipeline(self.storage_file, symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_class_based_pipeline_integration(self):
        symbol = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        percentage = round(random.uniform(5.0, 25.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2)]

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

if __name__ == "__main__":
    unittest.main()