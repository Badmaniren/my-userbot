import unittest
from unittest.mock import patch, mock_open
import json
import os
import io
import uuid
import random
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.window_size = random.randint(3, 10)
        self.smoothing_factor = round(random.uniform(0.1, 0.9), 2)
        self.calculator = RepoHealthTrendCalculator(window_size=self.window_size, smoothing_factor=self.smoothing_factor)
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.other_metric = f"metric_{uuid.uuid4().hex[:8]}"
        self.repo_id = uuid.uuid4().hex

    def test_init_properties(self):
        self.assertEqual(self.calculator.window_size, self.window_size)
        self.assertEqual(self.calculator.smoothing_factor, self.smoothing_factor)

    def test_calculate_metric_trend_empty_history(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_metric_trend([], self.metric_name)

    def test_calculate_metric_trend_missing_metric(self):
        history = [{"metrics": {self.other_metric: random.randint(1, 100)}}]
        with self.assertRaises(KeyError):
            self.calculator.calculate_metric_trend(history, self.metric_name)

    def test_calculate_metric_trend_improving(self):
        val1 = random.randint(10, 50)
        val2 = val1 + random.randint(10, 50)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["metric"], self.metric_name)
        self.assertEqual(result["direction"], "improving")
        self.assertEqual(result["latest_value"], val2)
        self.assertEqual(result["first_value"], val1)
        self.assertEqual(result["delta"], val2 - val1)
        self.assertGreater(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_degrading(self):
        val1 = random.randint(50, 100)
        val2 = val1 - random.randint(10, 40)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["metric"], self.metric_name)
        self.assertEqual(result["direction"], "degrading")
        self.assertEqual(result["latest_value"], val2)
        self.assertEqual(result["first_value"], val1)
        self.assertEqual(result["delta"], val2 - val1)
        self.assertLess(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_stable(self):
        val1 = random.randint(10, 100)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val1}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["direction"], "stable")
        self.assertEqual(result["delta"], 0)
        self.assertEqual(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_zero_first_value(self):
        val2 = random.randint(10, 50)
        history = [
            {"metrics": {self.metric_name: 0}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["first_value"], 0)
        self.assertEqual(result["change_percentage"], val2 * 100.0)

    def test_detect_metric_anomalies_empty(self):
        self.assertEqual(self.calculator.detect_metric_anomalies([], self.metric_name), [])
        history = [{"metrics": {self.other_metric: 5}}]
        self.assertEqual(self.calculator.detect_metric_anomalies(history, self.metric_name), [])

    def test_detect_metric_anomalies_zero_std(self):
        val = random.randint(1, 100)
        history = [{"metrics": {self.metric_name: val}}, {"metrics": {self.metric_name: val}}]
        self.assertEqual(self.calculator.detect_metric_anomalies(history, self.metric_name), [])

    def test_detect_metric_anomalies_found(self):
        normal_val = 10
        anomaly_val = 1000
        history = [
            {"metrics": {self.metric_name: normal_val}},
            {"metrics": {self.metric_name: normal_val}},
            {"metrics": {self.metric_name: normal_val}},
            {"metrics": {self.metric_name: anomaly_val}}
        ]
        anomalies = self.calculator.detect_metric_anomalies(history, self.metric_name, z_threshold=1.0)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metrics"][self.metric_name], anomaly_val)

    def test_load_history_from_file(self):
        random_file = f"{uuid.uuid4().hex}.json"
        expected_data = [{"metrics": {self.metric_name: random.randint(1, 50)}}]
        file_content = json.dumps(expected_data)
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mocked_file:
            res = self.calculator.load_history_from_file(random_file)
            mocked_file.assert_called_once_with(random_file, "r", encoding="utf-8")
            self.assertEqual(res, expected_data)

    def test_export_trend_summary(self):
        output_path = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        history = [{"metrics": {self.metric_name: random.randint(1, 100)}}]
        
        with patch("os.makedirs") as mock_makedirs, patch("builtins.open", mock_open()) as mock_file:
            res = self.calculator.export_trend_summary(history, output_path)
            self.assertTrue(res)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once_with(output_path, "w", encoding="utf-8")

    def test_calculate_overall_trend_empty(self):
        res = self.calculator.calculate_overall_trend([])
        self.assertEqual(res, {"overall_status": "stable", "metric_summaries": {}})

    def test_calculate_overall_trend_mixed(self):
        metric1 = f"m1_{uuid.uuid4().hex[:4]}"
        metric2 = f"m2_{uuid.uuid4().hex[:4]}"
        history = [
            {"metrics": {metric1: 10, metric2: 100}},
            {"metrics": {metric1: 20, metric2: 50}}
        ]
        res = self.calculator.calculate_overall_trend(history)
        self.assertIn("overall_status", res)
        self.assertIn(metric1, res["metric_summaries"])
        self.assertIn(metric2, res["metric_summaries"])

    def test_get_smoothed_series_empty(self):
        self.assertEqual(self.calculator.get_smoothed_series([], self.metric_name), [])

    def test_get_smoothed_series_missing(self):
        history = [{"metrics": {self.other_metric: 10}}]
        with self.assertRaises(KeyError):
            self.calculator.get_smoothed_series(history, self.metric_name)

    def test_get_smoothed_series_calculation(self):
        v1 = random.randint(10, 20)
        v2 = random.randint(30, 50)
        history = [
            {"metrics": {self.metric_name: v1}},
            {"metrics": {self.metric_name: v2}}
        ]
        smoothed = self.calculator.get_smoothed_series(history, self.metric_name)
        self.assertEqual(len(smoothed), 2)
        self.assertEqual(smoothed[0], float(v1))
        expected_second = self.calculator.smoothing_factor * v2 + (1.0 - self.calculator.smoothing_factor) * float(v1)
        self.assertEqual(smoothed[1], float(expected_second))

    def test_calculate_trends_empty(self):
        res = self.calculator.calculate_trends(self.repo_id, [])
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["trends"], {})
        self.assertEqual(res["summary"]["overall_status"], "stable")

    def test_calculate_trends_populated(self):
        v1 = random.randint(1, 10)
        v2 = random.randint(20, 30)
        v3 = random.randint(40, 50)
        history = [
            {"metrics": {self.metric_name: v1}},
            {"metrics": {self.metric_name: v2}},
            {"metrics": {self.metric_name: v3}}
        ]
        res = self.calculator.calculate_trends(self.repo_id, history)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertIn(self.metric_name, res["trends"])
        self.assertEqual(res["trends"][self.metric_name]["delta"], v3 - v1)
        self.assertEqual(res["trends"][self.metric_name]["direction"], "upward")
        self.assertEqual(res["trends"][self.metric_name]["historical_values"], [v1, v2, v3])

    def test_calculate_trends_downward(self):
        v1 = random.randint(40, 50)
        v2 = random.randint(1, 10)
        history = [
            {"metrics": {self.metric_name: v1}},
            {"metrics": {self.metric_name: v2}}
        ]
        res = self.calculator.calculate_trends(self.repo_id, history)
        self.assertEqual(res["trends"][self.metric_name]["direction"], "downward")
        self.assertEqual(res["trends"][self.metric_name]["delta"], v2 - v1)

    def test_calculate_health_trends_functional(self):
        input_file = f"{uuid.uuid4().hex}.json"
        output_file = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        payload = {
            "repo_id": self.repo_id,
            "history": [
                {"metrics": {self.metric_name: 5}},
                {"metrics": {self.metric_name: 15}}
            ]
        }
        json_data = json.dumps(payload)

        with patch("builtins.open", mock_open(read_data=json_data)) as mock_file, \
             patch("os.makedirs") as mock_makedirs:
            
            result = calculate_health_trends(input_file, output_file)
            
            mock_makedirs.assert_called_once()
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertIn(self.metric_name, result["trends"])
            self.assertEqual(result["trends"][self.metric_name]["historical_values"], [5, 15])

if __name__ == "__main__":
    unittest.main()