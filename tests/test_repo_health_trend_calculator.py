import unittest
import json
import os
import uuid
import random
import io
from unittest.mock import patch, mock_open
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator, calculate_health_trends

class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.window_size = random.randint(1, 10)
        self.smoothing_factor = random.random()
        self.calculator = RepoHealthTrendCalculator(self.window_size, self.smoothing_factor)

    def test_calculate_metric_trend_logic(self):
        metric_name = uuid.uuid4().hex
        val1 = random.uniform(10.0, 50.0)
        val2 = val1 + random.uniform(10.0, 20.0)
        history = [
            {"metrics": {metric_name: val1}},
            {"metrics": {metric_name: val2}}
        ]
        
        result = self.calculator.calculate_metric_trend(history, metric_name)
        
        self.assertEqual(result["metric"], metric_name)
        self.assertEqual(result["latest_value"], val2)
        self.assertEqual(result["first_value"], val1)
        self.assertEqual(result["direction"], "improving")
        self.assertGreater(result["change_percentage"], 0)

    def test_detect_metric_anomalies_outlier(self):
        metric_name = uuid.uuid4().hex
        # Создаем ряд с явным выбросом
        history = [{"metrics": {metric_name: 10.0}} for _ in range(10)]
        outlier_val = 100.0
        history.append({"metrics": {metric_name: outlier_val}})
        
        anomalies = self.calculator.detect_metric_anomalies(history, metric_name, z_threshold=1.0)
        
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metrics"][metric_name], outlier_val)

    def test_get_smoothed_series_calculation(self):
        metric_name = uuid.uuid4().hex
        vals = [random.uniform(1, 100) for _ in range(5)]
        history = [{"metrics": {metric_name: v}} for v in vals]
        
        smoothed = self.calculator.get_smoothed_series(history, metric_name)
        
        self.assertEqual(len(smoothed), len(vals))
        self.assertEqual(smoothed[0], float(vals[0]))
        # Проверка рекурсивной формулы сглаживания
        expected_second = self.smoothing_factor * vals[1] + (1.0 - self.smoothing_factor) * smoothed[0]
        self.assertAlmostEqual(smoothed[1], expected_second)

    def test_calculate_trends_structure(self):
        repo_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        history = [{"metrics": {metric_name: random.randint(1, 100)}} for _ in range(3)]
        
        result = self.calculator.calculate_trends(repo_id, history)
        
        self.assertEqual(result["repo_id"], repo_id)
        self.assertIn(metric_name, result["trends"])
        self.assertIn("summary", result)

    def test_calculate_health_trends_file_io(self):
        input_path = f"/{uuid.uuid4().hex}.json"
        output_path = f"/{uuid.uuid4().hex}.json"
        repo_id = uuid.uuid4().hex
        data = {"repo_id": repo_id, "history": [{"metrics": {"test": 10}}]}
        json_data = json.dumps(data)
        
        with patch("builtins.open", mock_open(read_data=json_data)) as mocked_file:
            with patch("os.makedirs"):
                with patch("json.dump") as mocked_json_dump:
                    result = calculate_health_trends(input_path, output_path)
                    
                    self.assertEqual(result["repo_id"], repo_id)
                    mocked_file.assert_any_call(input_path, "r", encoding="utf-8")
                    mocked_json_dump.assert_called_once()

    def test_empty_history_raises_error(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_metric_trend([], uuid.uuid4().hex)

    def test_missing_metric_raises_keyerror(self):
        history = [{"metrics": {uuid.uuid4().hex: 1}}]
        with self.assertRaises(KeyError):
            self.calculator.calculate_metric_trend(history, uuid.uuid4().hex)

    def test_overall_trend_logic(self):
        history = [
            {"metrics": {"a": 10, "b": 100}},
            {"metrics": {"a": 20, "b": 50}}
        ]
        # a: improving, b: degrading -> stable
        result = self.calculator.calculate_overall_trend(history)
        self.assertEqual(result["overall_status"], "stable")
        self.assertEqual(result["metric_summaries"]["a"]["direction"], "improving")
        self.assertEqual(result["metric_summaries"]["b"]["direction"], "degrading")

if __name__ == "__main__":
    unittest.main()