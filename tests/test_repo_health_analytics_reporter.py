import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.repo_health_analytics_reporter import RepoHealthAnalyticsReporter

class TestRepoHealthAnalyticsReporter(unittest.TestCase):

    def setUp(self):
        self.reporter = RepoHealthAnalyticsReporter()
        self.random_repo_name = f"repo_{uuid.uuid4().hex[:8]}"
        self.random_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.random_metric_value = random.randint(10, 1000)
        self.random_export_path = f"/tmp/{uuid.uuid4().hex}.json"
        
        self.sample_aggregated_data = {
            "repository": self.random_repo_name,
            "metrics": {
                self.random_metric_key: self.random_metric_value,
                f"secondary_{uuid.uuid4().hex[:4]}": random.random()
            },
            "status": random.choice(["HEALTHY", "CRITICAL", "WARNING"]),
            "timestamp": random.randint(1600000000, 1700000000)
        }

    def test_generate_report_success(self):
        report = self.reporter.generate_report(self.sample_aggregated_data)
        
        self.assertIsInstance(report, dict)
        self.assertIn("summary", report)
        self.assertIn("details", report)
        self.assertEqual(report["details"]["repository"], self.sample_aggregated_data["repository"])
        self.assertEqual(
            report["details"]["metrics"][self.random_metric_key], 
            self.random_metric_value
        )

    def test_generate_report_malformed_data(self):
        bad_data = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.randint(1, 100)
        }
        with self.assertRaises((KeyError, ValueError, TypeError)):
            self.reporter.generate_report(bad_data)

    def test_export_report_to_json_file(self):
        report_data = self.reporter.generate_report(self.sample_aggregated_data)
        mock_file = MagicMock()
        
        with patch("builtins.open", return_value=mock_file) as mock_open:
            result_path = self.reporter.export_report(report_data, self.random_export_path, format="json")
            
            mock_open.assert_called_once_with(self.random_export_path, "w", encoding="utf-8")
            self.assertEqual(result_path, self.random_export_path)
            
            written_content = "".join(call.args[0] for call in mock_file.__enter__().write.call_args_list)
            parsed_content = json.loads(written_content)
            self.assertEqual(parsed_content["details"]["repository"], self.sample_aggregated_data["repository"])

    def test_export_report_stream_bytes(self):
        report_data = self.reporter.generate_report(self.sample_aggregated_data)
        random_stream_id = uuid.uuid4().hex
        
        mock_stream = io.BytesIO()
        with patch("skills.repo_health_analytics_reporter.io.BytesIO", return_value=mock_stream):
            stream_result = self.reporter.export_to_stream(report_data, format="bytes")
            
            self.assertIsInstance(stream_result, io.BytesIO)
            stream_result.seek(0)
            content = stream_result.read().decode("utf-8")
            self.assertIn(self.sample_aggregated_data["repository"], content)

    def test_analytics_metrics_calculation_accuracy(self):
        local_metric_key = f"score_{uuid.uuid4().hex[:5]}"
        local_metric_val = random.randint(50, 500)
        
        custom_data = {
            "repository": f"ns_{uuid.uuid4().hex[:6]}",
            "metrics": {
                local_metric_key: local_metric_val
            },
            "status": "STABLE",
            "timestamp": 1650000000
        }
        
        report = self.reporter.generate_report(custom_data)
        calculated_score = report.get("analytics", {}).get("calculated_score")
        
        self.assertIsNotNone(calculated_score)
        self.assertGreaterEqual(calculated_score, 0)

    def test_export_unsupported_format(self):
        report_data = self.reporter.generate_report(self.sample_aggregated_data)
        unsupported_fmt = "".join(random.choices(string.ascii_lowercase, k=4))
        
        with self.assertRaises(ValueError):
            self.reporter.export_report(report_data, self.random_export_path, format=unsupported_fmt)

if __name__ == "__main__":
    unittest.main()