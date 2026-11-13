import unittest
from unittest.mock import patch, mock_open
import json
import os
import uuid
import random
import io

from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.window_size = random.randint(3, 10)
        self.smoothing_factor = round(random.uniform(0.1, 0.9), 2)
        self.calculator = RepoHealthTrendCalculator(window_size=self.window_size, smoothing_factor=self.smoothing_factor)
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.repo_id = uuid.uuid4().hex

    def test_init_properties(self):
        ws = random.randint(1, 20)
        sf = round(random.uniform(0.0, 1.0), 2)
        calc = RepoHealthTrendCalculator(window_size=ws, smoothing_factor=sf)
        self.assertEqual(calc.window_size, ws)
        self.assertEqual(calc.smoothing_factor, sf)

    def test_calculate_metric_trend_empty_history(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_metric_trend([], self.metric_name)

    def test_calculate_metric_trend_missing_metric(self):
        other_metric = f"metric_{uuid.uuid4().hex[:6]}"
        history = [{"metrics": {other_metric: random.randint(10, 100)}}]
        with self.assertRaises(KeyError):
            self.calculator.calculate_metric_trend(history, self.metric_name)

    def test_calculate_metric_trend_improving(self):
        val1 = random.randint(1, 50)
        val2 = val1 + random.randint(1, 50)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        res = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(res["metric"], self.metric_name)
        self.assertEqual(res["direction"], "improving")
        self.assertEqual(res["latest_value"], val2)
        self.assertEqual(res["first_value"], val1)
        self.assertEqual(res["delta"], val2 - val1)
        self.assertGreater(res["change_percentage"], 0.0)

    def test_calculate_metric_trend_degrading(self):
        val1 = random.randint(50, 100)
        val2 = val1 - random.randint(1, 49)
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        res = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(res["direction"], "degrading")
        self.assertLess(res["change_percentage"], 0.0)

    def test_calculate_metric_trend_stable(self):
        val = random.randint(1, 100)
        history = [
            {"metrics": {self.metric_name: val}},
            {"metrics": {self.metric_name: val}}
        ]
        res = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(res["direction"], "stable")
        self.assertEqual(res["change_percentage"], 0.0)

    def test_calculate_metric_trend_zero_first_value(self):
        val2 = random.randint(1, 100)
        history = [
            {"metrics": {self.metric_name: 0}},
            {"metrics": {self.metric_name: val2}}
        ]
        res = self.calculator.calculate_metric_trend(history, self.metric_name)
        self.assertEqual(res["first_value"], 0)
        self.assertEqual(res["change_percentage"], val2 * 100.0)

    def test_detect_metric_anomalies_empty(self):
        anomalies = self.calculator.detect_metric_anomalies([], self.metric_name)
        self.assertEqual(anomalies, [])

        anomalies_no_metric = self.calculator.detect_metric_anomalies([{"metrics": {}}], self.metric_name)
        self.assertEqual(anomalies_no_metric, [])

    def test_detect_metric_anomalies_zero_std_dev(self):
        val = random.randint(1, 100)
        history = [
            {"metrics": {self.metric_name: val}},
            {"metrics": {self.metric_name: val}}
        ]
        anomalies = self.calculator.detect_metric_anomalies(history, self.metric_name)
        self.assertEqual(anomalies, [])

    def test_detect_metric_anomalies_found(self):
        history = [
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 1000}} # anomaly
        ]
        anomalies = self.calculator.detect_metric_anomalies(history, self.metric_name, z_threshold=1.0)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metrics"][self.metric_name], 1000)

    def test_load_history_from_file(self):
        file_path = f"{uuid.uuid4().hex}.json"
        data = {"repo_id": self.repo_id, "history": []}
        file_content = json.dumps(data)

        with patch("builtins.open", mock_open(read_data=file_content)):
            loaded = self.calculator.load_history_from_file(file_path)
            self.assertEqual(loaded, data)

    def test_export_trend_summary(self):
        output_path = f"dir_{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        history = [{"metrics": {self.metric_name: random.randint(1, 100)}}]

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

    def test_calculate_overall_trend_improving_vs_degrading(self):
        m1 = f"m_{uuid.uuid4().hex[:4]}"
        m2 = f"m_{uuid.uuid4().hex[:4]}"
        history = [
            {"metrics": {m1: 10, m2: 50}},
            {"metrics": {m1: 20, m2: 25}}
        ]
        res = self.calculator.calculate_overall_trend(history)
        self.assertIn(res["overall_status"], ["improving", "degrading", "stable"])
        self.assertIn(m1, res["metric_summaries"])
        self.assertIn(m2, res["metric_summaries"])

    def test_get_smoothed_series_empty_and_missing(self):
        self.assertEqual(self.calculator.get_smoothed_series([], self.metric_name), [])
        with self.assertRaises(KeyError):
            self.calculator.get_smoothed_series([{"metrics": {}}], self.metric_name)

    def test_get_smoothed_series_values(self):
        history = [
            {"metrics": {self.metric_name: 10}},
            {"metrics": {self.metric_name: 20}},
            {"metrics": {self.metric_name: 30}}
        ]
        smoothed = self.calculator.get_smoothed_series(history, self.metric_name)
        self.assertEqual(len(smoothed), 3)
        self.assertEqual(smoothed[0], 10.0)

    def test_calculate_trends_empty(self):
        res = self.calculator.calculate_trends(self.repo_id, [])
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["trends"], {})
        self.assertEqual(res["summary"]["overall_status"], "stable")

    def test_calculate_trends_with_data(self):
        v1 = random.randint(1, 50)
        v2 = v1 + random.randint(1, 50)
        history = [
            {"metrics": {self.metric_name: v1}},
            {"metrics": {self.metric_name: v2}}
        ]
        res = self.calculator.calculate_trends(self.repo_id, history)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertIn(self.metric_name, res["trends"])
        self.assertEqual(res["trends"][self.metric_name]["direction"], "upward")
        self.assertEqual(res["trends"][self.metric_name]["delta"], v2 - v1)

    def test_calculate_trends_downward_and_stable(self):
        v1 = random.randint(50, 100)
        v2 = v1 - random.randint(1, 49)
        history_down = [
            {"metrics": {self.metric_name: v1}},
            {"metrics": {self.metric_name: v2}}
        ]
        res_down = self.calculator.calculate_trends(self.repo_id, history_down)
        self.assertEqual(res_down["trends"][self.metric_name]["direction"], "downward")

        v_stable = random.randint(1, 100)
        history_stable = [
            {"metrics": {self.metric_name: v_stable}},
            {"metrics": {self.metric_name: v_stable}}
        ]
        res_stable = self.calculator.calculate_trends(self.repo_id, history_stable)
        self.assertEqual(res_stable["trends"][self.metric_name]["direction"], "stable")

        history_single = [{"metrics": {self.metric_name: v_stable}}]
        res_single = self.calculator.calculate_trends(self.repo_id, history_single)
        self.assertEqual(res_single["trends"][self.metric_name]["direction"], "stable")

    def test_calculate_health_trends_function(self):
        input_file = f"{uuid.uuid4().hex}.json"
        output_file = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        input_data = {
            "repo_id": self.repo_id,
            "history": [
                {"metrics": {self.metric_name: 10}},
                {"metrics": {self.metric_name: 20}}
            ]
        }
        file_content = json.dumps(input_data)

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file, \
             patch("os.makedirs") as mock_makedirs:
            result = calculate_health_trends(input_file, output_file)
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertIn(self.metric_name, result["trends"])
            mock_makedirs.assert_called_once()
            self.assertGreaterEqual(mock_file.call_count, 2)