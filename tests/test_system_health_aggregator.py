import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_format = random.choice(['json', 'html'])
        self.random_path = f"/tmp/{uuid.uuid4().hex}.{self.random_format}"
        self.random_metric_key = uuid.uuid4().hex
        self.random_metric_value = random.randint(100, 9999)

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    @patch('skills.system_health_aggregator.RecoveryDashboardGenerator')
    def test_aggregate_and_report_success(self, mock_dashboard_gen_cls, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        mock_dashboard_instance = mock_dashboard_gen_cls.return_value

        expected_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_dashboard = uuid.uuid4().hex
        expected_system_health = {uuid.uuid4().hex: random.randint(1, 50)}

        mock_reporter_instance.generate_health_report.return_value = expected_report
        mock_dashboard_instance.aggregate_system_health.return_value = expected_system_health
        mock_dashboard_instance.generate_dashboard.return_value = expected_dashboard

        incidents = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        audit = {uuid.uuid4().hex: random.choice([True, False])}
        metrics = {self.random_metric_key: self.random_metric_value}

        result = self.aggregator.collect_and_aggregate(
            module_name=self.random_module,
            incident_data=incidents,
            audit_summary=audit,
            metrics=metrics,
            dashboard_format=self.random_format
        )

        mock_reporter_instance.generate_health_report.assert_called_once_with(
            self.random_module, incidents, audit, metrics
        )
        mock_dashboard_instance.aggregate_system_health.assert_called_once()
        mock_dashboard_instance.generate_dashboard.assert_called_once()

        self.assertIn('report', result)
        self.assertIn('dashboard', result)
        self.assertEqual(result['report'], expected_report)
        self.assertEqual(result['dashboard'], expected_dashboard)

    @patch('skills.system_health_aggregator.RecoveryDashboardGenerator')
    def test_parse_and_export_stream_data(self, mock_dashboard_gen_cls):
        mock_dashboard_instance = mock_dashboard_gen_cls.return_value
        parsed_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_dashboard_instance.parse_stream_data.return_value = parsed_data
        mock_dashboard_instance.export_dashboard.return_value = True

        random_stream_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_stream_bytes)

        result_parse = self.aggregator.process_stream(stream, self.random_path)

        mock_dashboard_instance.parse_stream_data.assert_called_once_with(random_stream_bytes)
        mock_dashboard_instance.export_dashboard.assert_called_once_with(parsed_data, self.random_path)
        self.assertTrue(result_parse)

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    def test_aggregate_system_metrics_delegation(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        aggregated_result = {uuid.uuid4().hex: random.randint(10, 100)}
        mock_reporter_instance.aggregate_system_metrics.return_value = aggregated_result

        incidents_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]

        result = self.aggregator.aggregate_metrics_from_lists(incidents_list, patches_list)

        mock_reporter_instance.aggregate_system_metrics.assert_called_once_with(incidents_list, patches_list)
        self.assertEqual(result, aggregated_result)

    @patch('skills.system_health_aggregator.RecoveryDashboardGenerator')
    def test_export_dashboard_file_delegation(self, mock_dashboard_gen_cls):
        mock_dashboard_instance = mock_dashboard_gen_cls.return_value
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.aggregator.save_dashboard_file(payload, self.random_path)

        mock_dashboard_instance.export_dashboard_file.assert_called_once_with(payload, self.random_path)

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    def test_export_health_report_file_delegation(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        health_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.aggregator.save_health_report(health_report, self.random_path)

        mock_reporter_instance.export_health_report.assert_called_once_with(health_report, self.random_path)

    @patch('skills.system_health_aggregator.SystemHealthReporter')
    def test_parse_stream_data_reporter_delegation(self, mock_reporter_cls):
        mock_reporter_instance = mock_reporter_cls.return_value
        expected_parsed = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_reporter_instance.parse_stream_data.return_value = expected_parsed

        random_stream_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_stream_bytes)

        result = self.aggregator.parse_reporter_stream(stream)

        mock_reporter_instance.parse_stream_data.assert_called_once_with(stream)
        self.assertEqual(result, expected_parsed)