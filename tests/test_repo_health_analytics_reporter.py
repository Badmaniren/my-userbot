import unittest
from unittest.mock import patch, mock_open
import io
import json
import os
import random
import uuid

from skills.repo_health_analytics_reporter import (
    RepoHealthAnalyticsReporter,
    generate_and_export_repo_health_analytics_report
)

class TestRepoHealthAnalyticsReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = RepoHealthAnalyticsReporter()
        self.repo_id = uuid.uuid4().hex
        self.status = random.choice(["HEALTHY", "WARNING", "CRITICAL"])
        self.timestamp = random.randint(1500000000, 1800000000)
        self.metric_key_1 = uuid.uuid4().hex
        self.metric_key_2 = uuid.uuid4().hex
        self.metric_val_1 = round(random.uniform(1.0, 100.0), 2)
        self.metric_val_2 = round(random.uniform(1.0, 100.0), 2)
        
        self.valid_data = {
            "repository": self.repo_id,
            "metrics": {
                self.metric_key_1: self.metric_val_1,
                self.metric_key_2: self.metric_val_2
            },
            "status": self.status,
            "timestamp": self.timestamp
        }
        self.file_path = f"{uuid.uuid4().hex}.json"

    def test_generate_report_success(self):
        report = self.reporter.generate_report(self.valid_data)
        
        self.assertEqual(report["summary"]["status"], self.status)
        self.assertEqual(report["summary"]["timestamp"], self.timestamp)
        self.assertEqual(report["details"]["repository"], self.repo_id)
        self.assertEqual(report["details"]["metrics"], self.valid_data["metrics"])
        
        expected_score = self.metric_val_1 + self.metric_val_2
        self.assertAlmostEqual(report["analytics"]["calculated_score"], expected_score)

    def test_generate_report_invalid_type(self):
        invalid_inputs = [random.randint(1, 1000), uuid.uuid4().hex, [1, 2, 3], None]
        for item in invalid_inputs:
            with self.assertRaises(TypeError):
                self.reporter.generate_report(item)

    def test_generate_report_missing_keys(self):
        required_keys = ["repository", "metrics", "status", "timestamp"]
        for key in required_keys:
            broken_data = self.valid_data.copy()
            del broken_data[key]
            with self.assertRaises(KeyError):
                self.reporter.generate_report(broken_data)

    def test_generate_report_invalid_metrics(self):
        invalid_metrics = [{}, [], uuid.uuid4().hex, None]
        for m in invalid_metrics:
            broken_data = self.valid_data.copy()
            broken_data["metrics"] = m
            with self.assertRaises(ValueError):
                self.reporter.generate_report(broken_data)

    def test_export_report_success(self):
        report_data = self.reporter.generate_report(self.valid_data)
        
        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.reporter.export_report(report_data, self.file_path, format="json")
            
            self.assertEqual(result_path, self.file_path)
            mocked_file.assert_called_once_with(self.file_path, "w", encoding="utf-8")
            
            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_content = json.loads(written_content)
            self.assertEqual(parsed_content["details"]["repository"], self.repo_id)

    def test_export_report_invalid_format(self):
        report_data = self.reporter.generate_report(self.valid_data)
        bad_format = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            self.reporter.export_report(report_data, self.file_path, format=bad_format)

    def test_export_to_stream(self):
        report_data = self.reporter.generate_report(self.valid_data)
        stream = self.reporter.export_to_stream(report_data, format="bytes")
        
        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read()
        parsed = json.loads(content.decode("utf-8"))
        self.assertEqual(parsed["summary"]["status"], self.status)
        self.assertEqual(parsed["details"]["repository"], self.repo_id)

    def test_generate_and_export_repo_health_analytics_report_function(self):
        collected_metrics = {
            "metrics": {
                self.metric_key_1: self.metric_val_1
            },
            "status": self.status,
            "timestamp": self.timestamp
        }
        trend_analysis = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        
        with patch("builtins.open", mock_open()) as mocked_file:
            result = generate_and_export_repo_health_analytics_report(
                repo_id=self.repo_id,
                collected_metrics=collected_metrics,
                trend_analysis=trend_analysis,
                destination_file=self.file_path
            )
            
            self.assertTrue(result["success"])
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["destination_file"], self.file_path)
            mocked_file.assert_called_once_with(self.file_path, "w", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()