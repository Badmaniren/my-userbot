import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.json"
        
        initial_data = {
            "symbol": "AAPL",
            "portfolio": {
                "AAPL": {"shares": 100, "price": 150.0}
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_class_execution(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2), round(random.uniform(-20.0, 20.0), 2)]

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_pipeline_functional_execution_with_random_data(self):
        symbol = f"TICKER_{uuid.uuid4().hex[:4]}"
        percentage = round(random.uniform(-30.0, 30.0), 2)
        shifts = [random.randint(-15, 15), random.randint(-25, 25)]

        result = run_stress_scenario_pipeline(self.storage_file, symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            self.assertIsInstance(data, dict)

    def test_pipeline_resilience_to_corrupted_storage(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("CORRUPTED_JSON_DATA_{{{")

        symbol = f"CORR_{uuid.uuid4().hex[:4]}"
        percentage = round(random.uniform(-10.0, 10.0), 2)
        shifts = [5, 10, 15]

        result = run_stress_scenario_pipeline(self.storage_file, symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            repaired_data = json.load(f)
            self.assertEqual(repaired_data, {})

if __name__ == "__main__":
    unittest.main()