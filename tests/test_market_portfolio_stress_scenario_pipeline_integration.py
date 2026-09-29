import unittest
import json
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        
        self.initial_data = {
            "cash": round(random.uniform(1000.0, 50000.0), 2),
            "positions": {
                "AAPL": {"shares": random.randint(1, 100), "avg_price": round(random.uniform(100.0, 200.0), 2)}
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_pipeline_class_execution(self):
        symbol = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2), round(random.uniform(-20.0, 20.0), 2)]

        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        result = pipeline.execute(symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_pipeline_function_execution_random_data(self):
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        percentage = round(random.uniform(-30.0, 30.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2) for _ in range(random.randint(1, 3))]

        result = run_stress_scenario_pipeline(self.storage_file, symbol, percentage, shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = json.load(f)
        self.assertIsInstance(content, dict)

if __name__ == "__main__":
    unittest.main()