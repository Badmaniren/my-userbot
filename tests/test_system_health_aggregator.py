import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator


class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_metric_key = uuid.uuid4().hex
        self.random_metric_val = random.randint(100, 9999)
        self.random_incident_id = uuid.uuid4().hex
        self.random_format = random.choice(['json', 'html'])
        self.random_path = f"/tmp/{uuid.uuid4().hex}.{self.random_format}"

    def test_composition_and_initialization(self):
        self.assertIsInstance(self.aggregator.health_reporter, SystemHealthReporter)
        self.assertIsInstance(self.aggregator.dashboard_generator, RecoveryDashboardGenerator)

    def test_aggregate_complex_health_report_success(self):
        mock_metrics = {self.random_metric_key: self.random_metric_val}
        mock_incidents = [{"id": self.random_incident_id, "status": "resolved"}]
        mock_reports = [uuid.uuid4().hex]

        with patch.object(SystemHealthReporter, 'aggregate_system_metrics', return_value=mock_metrics) as mock_agg_metrics, \
             patch.object(RecoveryDashboardGenerator, 'aggregate_system_health', return_value={"status": "optimal"}) as mock_agg_health, \
             patch.object(SystemHealthReporter, 'generate_health_report', return_value=mock_reports[0]) as mock_gen_report:

            result = self.aggregator.aggregate_complex_health(self.random_module, mock_incidents, [])

            mock_agg_metrics.assert_called_once_with(mock_incidents, [])
            mock_agg_health.assert_called_once()
            mock_gen_report.assert_called_once()
            self.assertIn("report", result)
            self.assertEqual(result["report"], mock_reports[0])

    def test_generate_and_export_dashboard_stream(self):
        stream_content = json.dumps({
            uuid.uuid4().hex: random.randint(1, 100)
        }).encode('utf-8')
        stream_mock = io.BytesIO(stream_content)

        metrics = {uuid.uuid4().hex: random.random()}
        incidents = [uuid.uuid4().hex]
        reports = [uuid.uuid4().hex]

        with patch.object(RecoveryDashboardGenerator, 'parse_stream_data', return_value=metrics) as mock_parse, \
             patch.object(RecoveryDashboardGenerator, 'generate_dashboard', return_value="dashboard_html_string") as mock_gen_dash, \
             patch.object(RecoveryDashboardGenerator, 'export_dashboard_file', return_value=True) as mock_export:

            res = self.aggregator.process_stream_and_export(stream_mock, incidents, reports, self.random_format, self.random_path)

            mock_parse.assert_called_once_with(stream_content)
            mock_gen_dash.assert_called_once_with(metrics, incidents, reports, self.random_format)
            mock_export.assert_called_once()
            self.assertTrue(res)

    def test_aggregate_system_health_failure_handling(self):
        with patch.object(RecoveryDashboardGenerator, 'aggregate_system_health', side_effect=Exception("Database connection timeout")) as mock_fail:
            with self.assertRaises(Exception) as ctx:
                self.aggregator.aggregate_complex_health(self.random_module, [], [])

            mock_fail.assert_called_once()
            self.assertIn("Database connection timeout", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()