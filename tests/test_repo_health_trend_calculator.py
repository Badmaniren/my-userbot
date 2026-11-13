import unittest
from unittest.mock import patch, mock_open
import json
import os
import random
import uuid
import io

from skills.repo_health_trend_calculator import (
    RepoHealthTrendCalculator,
    calculate_health_trends,
)


class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.window_size = random.randint(3, 10)
        self.smoothing_factor = round(random.uniform(0.1, 0.9), 2)
        self.calculator = RepoHealthTrendCalculator(
            window_size=self.window_size,
            smoothing_factor=self.smoothing_factor
        )
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.repo_id = f"repo_{uuid.uuid4().hex[:8]}"

    def test_init_properties(self):
        ws = random.randint(2, 20)
        sf = round(random.uniform(0.1, 0.9), 2)
        calc = RepoHealthTrendCalculator(window_size=ws, smoothing_factor=sf)
        self.assertEqual(calc.window_size, ws)
        self.assertEqual(calc.smoothing_factor, sf)

    def test_calculate_metric_trend_empty_history(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_metric_trend([], self.metric_name)

    def test_calculate_metric_trend_missing_metric(self):
        bad_metric = f"missing_{uuid.uuid4().hex[:4]}"
        history = [{"metrics": {self.metric_name: random.randint(10, 50)}}]
        with self.assertRaises(KeyError):
            self.calculator.calculate_metric_trend(history, bad_metric)

    def test_calculate_metric_trend_improving(self):
        val1 = random.randint(10, 40)
        val2 = val1 + random.randint(10, 50)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["metric"], self.metric_name)
        self.assertEqual(result["direction"], "improving")
        self.assertEqual(result["first_value"], val1)
        self.assertEqual(result["latest_value"], val2)
        self.assertGreater(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_degrading(self):
        val1 = random.randint(50, 100)
        val2 = val1 - random.randint(10, 40)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["direction"], "degrading")
        self.assertLess(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_stable(self):
        val = random.randint(1, 100)
        history = [
            {"metrics": {self.metric_name: val}},
            {"metrics": {self.metric_name: val}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["direction"], "stable")
        self.assertEqual(result["change_percentage"], 0.0)

    def test_calculate_metric_trend_zero_division_handling(self):
        val = 0
        val2 = random.randint(1, 50)
        history = [
            {"metrics": {self.metric_name: val}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(result["first_value"], 0)
        self.assertEqual(result["change_percentage"], float(val2 * 100.0))

    def test_detect_metric_anomalies_empty(self):
        self.assertEqual(self.calculator.detect_metric_anomalies([], self.metric_name), [])
        history = [{"metrics": {f"other_{uuid.uuid4().hex[:4]}": 10}}]
        self.assertEqual(self.calculator.detect_metric_anomalies(history, self.metric_name), [])

    def test_detect_metric_anomalies_zero_std_dev(self):
        val = random.randint(10, 50)
        history = [{"metrics": {self.metric_name: val}} for _ in range(3)]
        self.assertEqual(self.calculator.detect_metric_anomalies(history, self.metric_name), [])

    def test_detect_metric_anomalies_found(self):
        history = [
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 11}},
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 100}}
        ]
        anomalies = self.calculator.detect_metric_anomalies(history, self.metric_name, z_threshold=1.5)
        self.assertTrue(len(anomalies) > 0)
        self.assertEqual(anomalies[-1]["metrics"][self.metric_name], 100)

    def test_load_history_from_file(self):
        file_path = f"path_{uuid.uuid4().hex}.json"
        mock_data = [{"metrics": {self.metric_name: random.randint(1, 100)}}]
        mock_file_content = json.dumps(mock_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)) as mocked_file:
            loaded = self.calculator.load_history_from_file(file_path)
            mocked_file.assert_called_once_with(file_path, "r", encoding="utf-8")
            self.assertEqual(loaded, mock_data)

    def test_export_trend_summary(self):
        output_path = f"dir_{uuid.uuid4().hex}/summary_{uuid.uuid4().hex}.json"
        history = [{"metrics": {self.metric_name: random.randint(10, 20)}}]

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            res = self.calculator.export_trend_summary(history, output_path)
            self.assertTrue(res)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once_with(output_path, "w", encoding="utf-8")

    def test_calculate_overall_trend_empty(self):
        res = self.calculator.calculate_overall_trend([])
        self.assertEqual(res["overall_status"], "stable")
        self.assertEqual(res["metric_summaries"], {})

    def test_calculate_overall_trend_mixed(self):
        m1 = f"m1_{uuid.uuid4().hex[:4]}"
        m2 = f"m2_{uuid.uuid4().hex[:4]}"
        history = [
            {"metrics": {m1: 10, m2: 100}},
            {"metrics": {m1: 20, m2: 50}}
        ]
        res = self.calculator.calculate_overall_trend(history)
        self.assertIn(m1, res["metric_summaries"])
        self.assertIn(m2, res["metric_summaries"])
        self.assertIn(res["overall_status"], ["improving", "degrading", "stable"])

    def test_get_smoothed_series(self):
        history = [
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 20}},
            {"metrics": {self.metric_name: 30}}
        ]
        smoothed = self.calculator.get_smoothed_series(history, self.metric_name)
        self.assertEqual(len(smoothed), 3)
        self.assertEqual(smoothed[0], 10.0)

    def test_get_smoothed_series_missing_metric(self):
        history = [{"metrics": {f"wrong_{uuid.uuid4().hex[:4]}": 15}}]
        with self.assertRaises(KeyError):
            self.calculator.get_smoothed_series(history, self.metric_name)

    def test_get_smoothed_series_empty(self):
        self.assertEqual(self.calculator.get_smoothed_series([], self.metric_name), [])

    def test_calculate_trends_empty(self):
        res = self.calculator.calculate_trends(self.repo_id, [])
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["trends"], {})
        self.assertEqual(res["summary"]["overall_status"], "stable")

    def test_calculate_trends_with_data(self):
        history = [
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 30}}
        ]
        res = self.calculator.calculate_trends(self.repo_id, history)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertIn(self.metric_name, res["trends"])
        self.assertEqual(res["trends"][self.metric_name]["direction"], "upward")
        self.assertEqual(res["trends"][self.metric_name]["delta"], 20)

    def test_calculate_health_trends_function(self):
        input_file = f"in_{uuid.uuid4().hex}.json"
        output_file = f"out_{uuid.uuid4().hex}.json"
        payload = {
            "repo_id": self.repo_id,
            "history": [
                {"metrics": {self.metric_name: 5}},
                {"metrics": {self.metric_name: 15}}
            ]
        }
        file_data = json.dumps(payload)

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file, \
             patch("os.makedirs") as mock_dirs:
            result = calculate_health_trends(input_file, output_file)
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertIn(self.metric_name, result["trends"])
            mock_dirs.assert_called_once()
            self.assertTrue(mock_file.call_count >= 2)


if __name__ == "__main__":
    unittest.main()