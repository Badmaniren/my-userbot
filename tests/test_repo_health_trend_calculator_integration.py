import unittest
import json
import os
import uuid
import random
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_workspace_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_file = os.path.join(self.test_dir, f"input_{uuid.uuid4().hex}.json")
        self.output_file = os.path.join(self.test_dir, f"output_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_health_trends_pipeline_and_calculator(self):
        repo_id = f"repo-{uuid.uuid4().hex[:8]}"
        metric_name = f"coverage_{random.randint(10, 99)}"
        
        base_value = random.uniform(50.0, 80.0)
        step_value = random.uniform(1.0, 5.0)
        
        history = []
        for i in range(5):
            val = base_value + (i * step_value)
            if i == 2:
                val += random.uniform(15.0, 30.0)
            history.append({
                "snapshot_id": str(uuid.uuid4()),
                "metrics": {
                    metric_name: round(val, 2)
                }
            })

        input_data = {
            "repo_id": repo_id,
            "history": history
        }

        with open(self.input_file, "w", encoding="utf-8") as f:
            json.dump(input_data, f, indent=2)

        result = calculate_health_trends(self.input_file, self.output_file)

        self.assertTrue(os.path.exists(self.output_file), "Output file was not created by the integration pipeline")

        with open(self.output_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("repo_id"), repo_id)
        self.assertIn("trends", persisted_data)
        self.assertIn("summary", persisted_data)
        self.assertIn(metric_name, persisted_data["trends"])

        calculator = RepoHealthTrendCalculator(window_size=3, smoothing_factor=0.4)
        
        metric_trend = calculator.calculate_metric_trend(history, metric_name)
        self.assertEqual(metric_trend["metric"], metric_name)
        self.assertIn("direction", metric_trend)
        self.assertIn("change_percentage", metric_trend)

        anomalies = calculator.detect_metric_anomalies(history, metric_name, z_threshold=1.0)
        self.assertIsInstance(anomalies, list)

        smoothed = calculator.get_smoothed_series(history, metric_name)
        self.assertEqual(len(smoothed), len(history))

        export_path = os.path.join(self.test_dir, f"summary_{uuid.uuid4().hex}.json")
        exported = calculator.export_trend_summary(history, export_path)
        self.assertTrue(exported)
        self.assertTrue(os.path.exists(export_path))

        if os.path.exists(export_path):
            os.remove(export_path)

if __name__ == "__main__":
    unittest.main()