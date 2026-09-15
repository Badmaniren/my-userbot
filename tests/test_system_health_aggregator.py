import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string

from skills.system_health_aggregator import SystemHealthAggregator


class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.random_module = f"module_{uuid.uuid4().hex[:8]}"
        self.random_path = f"/var/log/{uuid.uuid4().hex[:8]}.json"
        self.random_stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        
        self.random_metrics = {
            f"metric_{uuid.uuid4().hex[:4]}": random.randint(1, 100)
        }
        self.random_incidents = [
            {"id": uuid.uuid4().hex, "severity": random.choice(["LOW", "MEDIUM", "HIGH"])}
        ]
        self.random_patches = [
            {"patch_id": uuid.uuid4().hex, "status": random.choice(["applied", "pending"])}
        ]
        self.random_audit = {
            "status": random.choice(["passed", "failed"]),
            "score": random.random()
        }

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    @patch('skills.system_health_aggregator.RecoveryDashboardGenerator')
    def test_collect_and_aggregate_delegation(self, mock_dashboard_gen_cls, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        mock_dashboard_instance = mock_dashboard_gen_cls.return_value

        expected_report = {"report_id": uuid.uuid4().hex}
        expected_dashboard = {"dashboard_id": uuid.uuid4().hex}

        mock_reporter_instance.generate_health_report.return_value = expected_report
        mock_dashboard_instance.generate_dashboard.return_value = expected_dashboard

        aggregator = SystemHealthAggregator()
        result = aggregator.collect_and_aggregate(
            module_name=self.random_module,
            incident_data=self.random_incidents,
            audit_summary=self.random_audit,
            metrics=self.random_metrics,
            dashboard_format="json",
            incidents_list=self.random_incidents,
            patches_list=self.random_patches
        )

        mock_reporter_instance.generate_health_report.assert_called_once_with(
            self.random_module,
            self.random_incidents,
            self.random_audit,
            self.random_metrics
        )
        mock_dashboard_instance.aggregate_system_health.assert_called_once()
        mock_dashboard_instance.generate_dashboard.assert_called_once_with(
            metrics=self.random_metrics,
            incidents=self.random_incidents,
            reports=[expected_report],
            format="json"
        )

        self.assertEqual(result['report'], expected_report)
        self.assertEqual(result['dashboard'], expected_dashboard)

    @patch('skills.system_health_aggregator.RecoveryDashboardGenerator')
    def test_process_stream_delegation(self, mock_dashboard_gen_cls):
        mock_dashboard_instance = mock_dashboard_gen_cls.return_value
        parsed_mock_data = {"stream_key": uuid.uuid4().hex}
        mock_dashboard_instance.parse_stream_data.return_value = parsed_mock_data
        
        expected_export_result = random.choice([True, False])
        mock_dashboard_instance.export_dashboard.return_value = expected_export_result

        stream = io.BytesIO(self.random_stream_data)
        aggregator = SystemHealthAggregator()
        result = aggregator.process_stream(stream, self.random_path)

        mock_dashboard_instance.parse_stream_data.assert_called_once_with(self.random_stream_data)
        mock_dashboard_instance.export_dashboard.assert_called_once_with(
            json.dumps(parsed_mock_data), self.random_path
        )
        self.assertEqual(result, expected_export_result)

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    def test_aggregate_system_metrics_delegation(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        expected_aggregation = {"aggregated": uuid.uuid4().hex}
        mock_reporter_instance.aggregate_system_metrics.return_value = expected_aggregation

        aggregator = SystemHealthAggregator()
        result = aggregator.aggregate_metrics_from_lists(self.random_incidents, self.random_patches)

        mock_reporter_instance.aggregate_system_metrics.assert_called_once_with(
            self.random_incidents, self.random_patches
        )
        self.assertEqual(result, expected_aggregation)

    @patch('skills.system_health_aggregator.RecoveryDashboardGenerator')
    def test_save_dashboard_file_delegation(self, mock_dashboard_gen_cls):
        mock_dashboard_instance = mock_dashboard_gen_cls.return_value
        payload_dict = {"data_id": uuid.uuid4().hex}

        aggregator = SystemHealthAggregator()
        aggregator.save_dashboard_file(payload_dict, self.random_path)

        mock_dashboard_instance.export_dashboard_file.assert_called_once_with(
            json.dumps(payload_dict), self.random_path
        )

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    def test_save_health_report_delegation(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        report_dict = {"report_uuid": uuid.uuid4().hex}

        aggregator = SystemHealthAggregator()
        aggregator.save_health_report(report_dict, self.random_path)

        mock_reporter_instance.export_health_report.assert_called_once_with(
            json.dumps(report_dict), self.random_path
        )

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    def test_parse_reporter_stream_delegation(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        parsed_output = {"parsed_stream": uuid.uuid4().hex}
        mock_reporter_instance.parse_stream_data.return_value = parsed_output

        stream = io.BytesIO(self.random_stream_data)
        aggregator = SystemHealthAggregator()
        result = aggregator.parse_reporter_stream(stream)

        mock_reporter_instance.parse_stream_data.assert_called_once_with(stream)
        self.assertEqual(result, parsed_output)