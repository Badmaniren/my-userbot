import unittest
import json
import os
import uuid
import random
import io
from unittest.mock import patch, mock_open
from skills.repo_health_trend_calculator import RepoHealthTrendCalculator

class TestRepoHealthTrendCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = RepoHealthTrendCalculator(
            window_size=random.randint(1, 10),
            smoothing_factor=random.random()
        )
        self.metric_name = uuid.uuid4().hex
        self.history = [
            {"metrics": {self.metric_name: random.uniform(10, 50)}},
            {"metrics": {self.metric_name: random.uniform(50, 100)}}
        ]

    def test_calculate_metric_trend_logic(self):
        val1 = 10.0
        val2 = 20.0
        history = [
            {"metrics": {self.metric_name: val1}},
            {"metrics": {self.metric_name: val2}}
        ]
        result = self.calculator.calculate_metric_trend(history, self.metric_name)
        
        self.assertEqual(result["metric"], self.metric_name)
        self.assertEqual(result["first_value"], val1)
        self.assertEqual(result["latest_value"], val2)
        self.assertEqual(result["direction"], "improving")
        self.assertGreater(result["change_percentage"], 0)

    def test_detect_metric_anomalies_threshold(self):
        # Создаем данные с явным выбросом
        base_val = 100
        history = [{"metrics": {self.metric_name: base_val}} for _ in range(5)]
        anomaly_val = 1000.0
        history.append({"metrics": {self.metric_name: anomaly_val}})
        
        anomalies = self.calculator.detect_metric_anomalies(history, self.metric_name, z_threshold=1.0)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["metrics"][self.metric_name], anomaly_val)

    def test_load_history_from_file_io(self):
        file_path = f"{uuid.uuid4().hex}.json"
        mock_data = {"repo_id": uuid.uuid4().hex, "history": self.history}
        json_str = json.dumps(mock_data)
        
        with patch("builtins.open", mock_open(read_data=json_str)):
            data = self.calculator.load_history_from_file(file_path)
            self.assertEqual(data["repo_id"], mock_data["repo_id"])

    def test_export_trend_summary_directory_creation(self):
        output_path = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mocked_file:
            
            result = self.calculator.export_trend_summary(self.history, output_path)
            
            self.assertTrue(result)
            mock_makedirs.assert_called_once()
            mocked_file.assert_called_once()

    def test_calculate_trends_integrity(self):
        repo_id = uuid.uuid4().hex
        result = self.calculator.calculate_trends(repo_id, self.history)
        
        self.assertEqual(result["repo_id"], repo_id)
        self.assertIn(self.metric_name, result["trends"])
        self.assertIn("summary", result)
        self.assertIsInstance(result["trends"][self.metric_name]["historical_values"], list)

    def test_get_smoothed_series_calculation(self):
        values = [10.0, 20.0, 30.0]
        history = [{"metrics": {self.metric_name: v}} for v in values]
        self.calculator.smoothing_factor = 0.5
        
        smoothed = self.calculator.get_smoothed_series(history, self.metric_name)
        
        self.assertEqual(len(smoothed), 3)
        self.assertEqual(smoothed[0], 10.0)
        # 0.5 * 20 + (1-0.5) * 10 = 15.0
        self.assertEqual(smoothed[1], 15.0)
        # 0.5 * 30 + (1-0.5) * 15 = 22.5
        self.assertEqual(smoothed[2], 22.5)

    def test_calculate_metric_trend_empty_history_raises(self):
        with self.assertRaises(ValueError):
            self.calculator.calculate_metric_trend([], self.metric_name)

    def test_calculate_metric_trend_missing_key_raises(self):
        history = [{"metrics": {"wrong_key": 1}}]
        with self.assertRaises(KeyError):
            self.calculator.calculate_metric_trend(history, self.metric_name)

if __name__ == "__main__":
    unittest.main()