import unittest
import os
import json
import uuid
import random
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.input_file = f"test_input_{uuid.uuid4()}.json"
        self.output_file = f"test_output_{uuid.uuid4()}.json"
        self.calculator = RepoHealthTrendCalculator(window_size=random.randint(3, 10), smoothing_factor=0.7)

    def tearDown(self):
        for f_path in [self.input_file, self.output_file]:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_integration_full_trend_calculation_pipeline(self):
        val1 = random.randint(10, 50)
        val2 = val1 + random.randint(1, 20)
        val3 = val2 + random.randint(1, 30)

        history_data = [
            {"snapshot_id": str(uuid.uuid4()), "metrics": {self.metric_name: val1}},
            {"snapshot_id": str(uuid.uuid4()), "metrics": {self.metric_name: val2}},
            {"snapshot_id": str(uuid.uuid4()), "metrics": {self.metric_name: val3}}
        ]

        payload = {
            "repo_id": self.repo_id,
            "history": history_data
        }

        with open(self.input_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        result = calculate_health_trends(self.input_file, self.output_file)

        self.assertTrue(os.path.exists(self.output_file), "Output file was not created by the pipeline.")

        with open(self.output_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("repo_id"), self.repo_id)
        self.assertIn("trends", persisted_data)
        self.assertIn("summary", persisted_data)

        metric_trends = persisted_data["trends"].get(self.metric_name)
        self.assertIsNotNone(metric_trends)
        self.assertEqual(metric_trends["direction"], "upward")
        self.assertEqual(metric_trends["delta"], val3 - val1)
        self.assertEqual(metric_trends["historical_values"], [val1, val2, val3])

        summary = persisted_data["summary"]
        self.assertEqual(summary["overall_status"], "improving")
        self.assertIn(self.metric_name, summary["metric_summaries"])

        trend_summary = self.calculator.calculate_metric_trend(history_data, self.metric_name)
        self.assertEqual(trend_summary["first_value"], val1)
        self.assertEqual(trend_summary["latest_value"], val3)
        self.assertEqual(trend_summary["delta"], val3 - val1)
        self.assertEqual(trend_summary["direction"], "improving")

        smoothed = self.calculator.get_smoothed_series(history_data, self.metric_name)
        self.assertEqual(len(smoothed), 3)
        self.assertEqual(smoothed[0], float(val1))

        anomalies = self.calculator.detect_metric_anomalies(history_data, self.metric_name, z_threshold=10.0)
        self.assertIsInstance(anomalies, list)

        exported_path = f"test_export_{uuid.uuid4()}.json"
        try:
            export_success = self.calculator.export_trend_summary(history_data, exported_path)
            self.assertTrue(export_success)
            self.assertTrue(os.path.exists(exported_path))
        finally:
            if os.path.exists(exported_path):
                os.remove(exported_path)

if __name__ == "__main__":
    unittest.main()