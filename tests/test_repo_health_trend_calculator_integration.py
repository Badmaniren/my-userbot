import unittest
import os
import json
import uuid
import random
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.calculator = RepoHealthTrendCalculator(window_size=3, smoothing_factor=0.4)
        self.test_input_file = f"test_input_{uuid.uuid4()}.json"
        self.test_output_file = f"test_output_{uuid.uuid4()}.json"

    def tearDown(self):
        for file_path in [self.test_input_file, self.test_output_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_integration_full_trend_calculation_pipeline(self):
        random_repo_id = f"repo-{uuid.uuid4()}"
        base_metric_val = random.randint(50, 100)
        history_data = []

        for i in range(5):
            metric_val = base_metric_val + (i * random.randint(1, 10))
            history_data.append({
                "snapshot_id": str(uuid.uuid4()),
                "metrics": {
                    "coverage": float(metric_val),
                    "complexity": float(100 - metric_val)
                }
            })

        input_payload = {
            "repo_id": random_repo_id,
            "history": history_data
        }

        with open(self.test_input_file, "w", encoding="utf-8") as f:
            json.dump(input_payload, f)

        result = calculate_health_trends(self.test_input_file, self.test_output_file)

        self.assertTrue(os.path.exists(self.test_output_file))

        with open(self.test_output_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("repo_id"), random_repo_id)
        self.assertIn("trends", file_data)
        self.assertIn("summary", file_data)
        self.assertIn("coverage", file_data["trends"])
        self.assertIn("complexity", file_data["trends"])

        coverage_trend = file_data["trends"]["coverage"]
        self.assertEqual(coverage_trend["direction"], "upward")
        self.assertGreater(coverage_trend["delta"], 0)
        self.assertEqual(len(coverage_trend["historical_values"]), 5)

        summary = file_data["summary"]
        self.assertIn("overall_status", summary)
        self.assertIn("metric_summaries", summary)
        self.assertIn("coverage", summary["metric_summaries"])

        smoothed_series = self.calculator.get_smoothed_series(history_data, "coverage")
        self.assertEqual(len(smoothed_series), 5)

        anomalies = self.calculator.detect_metric_anomalies(history_data, "coverage", z_threshold=1.0)
        self.assertIsInstance(anomalies, list)

        export_success = self.calculator.export_trend_summary(history_data, self.test_output_file)
        self.assertTrue(export_success)

if __name__ == "__main__":
    unittest.main()