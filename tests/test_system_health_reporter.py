import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.system_health_reporter import SystemHealthReporter


class TestSystemHealthReporter(unittest.TestCase):

    def setUp(self):
        self.reporter = SystemHealthReporter()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_incident_id = uuid.uuid4().hex
        self.random_error_msg = ''.join(random.choices(string.ascii_letters, k=15))
        self.random_path = f"/tmp/{uuid.uuid4().hex}.json"

    def test_init(self):
        self.assertIsNotNone(self.reporter)

    def test_generate_health_report_success(self):
        metrics_data = {
            "module": self.random_module,
            "incident_id": self.random_incident_id,
            "error": self.random_error_msg,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        }
        
        with patch.object(self.reporter, '_collect_system_metrics', return_value=metrics_data) as mock_collect:
            report = self.reporter.generate_health_report(self.random_module)
            mock_collect.assert_called_once_with(self.random_module)
            self.assertIn(self.random_module, report)
            self.assertIn(self.random_incident_id, report)

    def test_parse_stream_data_bytes(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.printable, k=20)).encode('utf-8')
        stream = io.BytesIO(random_bytes)
        
        result = self.reporter.parse_stream_data(stream)
        self.assertIsInstance(result, dict)
        self.assertIn("raw_length", result)
        self.assertEqual(result["raw_length"], len(random_bytes))

    def test_parse_stream_data_invalid(self):
        stream = "Not a stream"
        result = self.reporter.parse_stream_data(stream)
        self.assertIsNone(result)

    def test_export_report_file(self):
        payload = {
            "incident_id": self.random_incident_id,
            "metrics": {
                "cpu_load": random.uniform(10.0, 99.9),
                "memory_leak": random.choice([True, False])
            }
        }
        
        mock_file_open = MagicMock()
        with patch("builtins.open", mock_file_open):
            success = self.reporter.export_report_file(payload, self.random_path)
            self.assertTrue(success)
            mock_file_open.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

    def test_export_report_file_exception(self):
        payload = {"error": self.random_error_msg}
        with patch("builtins.open", side_effect=Exception(self.random_error_msg)):
            success = self.reporter.export_report_file(payload, self.random_path)
            self.assertFalse(success)

    def test_aggregate_system_metrics(self):
        incidents_list = [
            {"incident_id": uuid.uuid4().hex, "resolved": random.choice([True, False])},
            {"incident_id": uuid.uuid4().hex, "resolved": random.choice([True, False])}
        ]
        patches_list = [
            {"patch_id": uuid.uuid4().hex, "success": True}
        ]
        
        aggregated = self.reporter.aggregate_system_metrics(incidents_list, patches_list)
        self.assertIsInstance(aggregated, dict)
        self.assertEqual(aggregated["total_incidents"], len(incidents_list))
        self.assertEqual(aggregated["total_patches"], len(patches_list))

    def test_generate_list_feed(self):
        telemetry_feed = [{"title": "Item 1", "link": "http://example.com/1"}]
        report = self.reporter.generate(telemetry_feed, module_name=self.random_module)
        self.assertIsInstance(report, dict)
        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["telemetry_feed"], telemetry_feed)
        self.assertEqual(report["metrics"]["feed_items"], 1)

    def test_generate_string_feed(self):
        telemetry_feed = "raw telemetry log"
        report = self.reporter.generate(telemetry_feed, module_name=self.random_module)
        self.assertIsInstance(report, str)
        self.assertIn(self.random_module, report)


if __name__ == "__main__":
    unittest.main()