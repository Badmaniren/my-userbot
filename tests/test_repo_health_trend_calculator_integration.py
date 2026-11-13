import unittest
import json
import os
import uuid
import random
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_data_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_file = os.path.join(self.test_dir, f"input_{uuid.uuid4().hex}.json")
        self.output_file = os.path.join(self.test_dir, f"output_{uuid.uuid4().hex}.json")
        
        self.repo_id = str(uuid.uuid4())
        self.metric_name = f"coverage_{uuid.uuid4().hex[:6]}"
        
        self.val1 = random.randint(10, 50)
        self.val2 = random.randint(51, 100)
        
        self.history = [
            {"timestamp": "2023-01-01T00:00:00Z", "metrics": {self.metric_name: self.val1}},
            {"timestamp": "2023-01-02T00:00:00Z", "metrics": {self.metric_name: self.val2}}
        ]
        
        self.input_data = {
            "repo_id": self.repo_id,
            "history": self.history
        }
        
        with open(self.input_file, "w", encoding="utf-8") as f:
            json.dump(self.input_data, f)

    def tearDown(self):
        for path in [self.input_file, self.output_file]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_calculate_health_trends_integration(self):
        result = calculate_health_trends(self.input_file, self.output_file)
        
        self.assertTrue(os.path.exists(self.output_file), "Output file was not created by integration function")
        
        with open(self.output_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
            
        self.assertEqual(persisted_data.get("repo_id"), self.repo_id)
        self.assertIn("trends", persisted_data)
        self.assertIn("summary", persisted_data)
        
        trends = persisted_data["trends"]
        self.assertIn(self.metric_name, trends)
        
        metric_trend = trends[self.metric_name]
        expected_delta = self.val2 - self.val1
        self.assertEqual(metric_trend["delta"], expected_delta)
        self.assertEqual(metric_trend["historical_values"], [self.val1, self.val2])
        
        calculator = RepoHealthTrendCalculator(smoothing_factor=0.7)
        smoothed = calculator.get_smoothed_series(self.history, self.metric_name)
        self.assertEqual(len(smoothed), 2)
        self.assertEqual(smoothed[0], float(self.val1))

if __name__ == "__main__":
    unittest.main()