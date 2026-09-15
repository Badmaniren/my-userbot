import io
import json
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.system_health_reporter import SystemHealthReporter


class TestSystemHealthReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = SystemHealthReporter()
        self.random_module = f"module_{uuid.uuid4().hex[:8]}"
        self.random_incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        self.random_error = f"ERR_{uuid.uuid4().hex[:6]}"
        self.random_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.random_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')

    def tearDown(self):
        if os.path.exists(self.random_path):
            try:
                os.remove(self.random_path)
            except OSError:
                pass

    def test_collect_system_metrics_structure(self):
        metrics = self.reporter._collect_system_metrics(self.random_module)
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["module"], self.random_module)
        self.assertEqual(metrics["incident_id"], "")
        self.assertEqual(metrics["error"], "")
        self.assertEqual(metrics["severity"], "LOW")

    @patch('skills.system_health_reporter.SystemHealthAggregator')
    @patch('skills.system_health_reporter.RecoveryReportExporter')
    def test_generate_health_report_delegation(self, mock_exporter_cls, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_dict = {
            "module": self.random_module,
            "status": "HEALTHY",
            "token": uuid.uuid4().hex
        }
        mock_aggregator_instance.collect_and_aggregate.return_value = expected_dict

        incident_data = {"incident_id": self.random_incident_id, "error": self.random_error}
        audit_summary = {"audit": random.randint(1, 100)}
        metrics = {"cpu": random.random()}

        result = self.reporter.generate_health_report(
            self.random_module,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics
        )

        mock_aggregator_instance.collect_and_aggregate.assert_called_once_with(
            self.random_module,
            incident_data,
            audit_summary,
            metrics,
            None,
            None,
            None
        )
        self.assertEqual(result, json.dumps(expected_dict, ensure_ascii=False))

    @patch('skills.system_health_reporter.SystemHealthAggregator')
    def test_parse_stream_data_valid(self, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_parsed = {
            "raw_length": len(self.random_stream_data),
            "data": self.random_stream_data,
            "random_flag": random.choice([True, False])
        }
        mock_aggregator_instance.parse_reporter_stream.return_value = expected_parsed

        stream = io.BytesIO(self.random_stream_data)
        result = self.reporter.parse_stream_data(stream)

        mock_aggregator_instance.parse_reporter_stream.assert_called_once_with(stream)
        self.assertEqual(result, expected_parsed)

    def test_parse_stream_data_invalid(self):
        invalid_stream = f"not_a_stream_{uuid.uuid4().hex}"
        result = self.reporter.parse_stream_data(invalid_stream)
        self.assertIsNone(result)

    @patch('skills.system_health_reporter.SystemHealthAggregator')
    def test_export_report_file_delegation(self, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        mock_aggregator_instance.save_dashboard_file.return_value = True

        payload = {"data": uuid.uuid4().hex}
        success = self.reporter.export_report_file(payload, self.random_path)

        mock_aggregator_instance.save_dashboard_file.assert_called_once_with(payload, self.random_path)
        self.assertTrue(success)

    @patch('skills.system_health_reporter.SystemHealthAggregator')
    def test_export_health_report_delegation(self, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        mock_aggregator_instance.save_health_report.return_value = True

        health_report = [{"report_id": uuid.uuid4().hex}]
        success = self.reporter.export_health_report(health_report, self.random_path)

        mock_aggregator_instance.save_health_report.assert_called_once_with(health_report, self.random_path)
        self.assertTrue(success)

    @patch('skills.system_health_reporter.SystemHealthAggregator')
    def test_aggregate_system_metrics_delegation(self, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_metrics = {
            "total_incidents": random.randint(5, 50),
            "total_patches": random.randint(1, 10)
        }
        mock_aggregator_instance.aggregate_system_metrics.return_value = expected_metrics

        incidents_list = [uuid.uuid4().hex for _ in range(expected_metrics["total_incidents"])]
        patches_list = [uuid.uuid4().hex for _ in range(expected_metrics["total_patches"])]

        result = self.reporter.aggregate_system_metrics(incidents_list, patches_list)

        mock_aggregator_instance.aggregate_system_metrics.assert_called_once_with(incidents_list, patches_list)
        self.assertEqual(result, expected_metrics)


if __name__ == '__main__':
    unittest.main()