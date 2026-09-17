import unittest
from unittest.mock import patch, MagicMock, mock_open
import uuid
import random
import string
import json
import io
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class TestSystemHealthTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.incident_data = {uuid.uuid4().hex: random.randint(1, 100)}
        self.audit_summary = f"audit_{uuid.uuid4().hex[:6]}"
        self.metrics = {uuid.uuid4().hex: random.random()}
        self.dashboard_format = f"format_{random.choice(['json', 'xml', 'yaml'])}"
        self.incidents_list = [uuid.uuid4().hex for _ in range(3)]
        self.patches_list = [uuid.uuid4().hex for _ in range(2)]
        self.report_path = f"/var/log/{uuid.uuid4().hex}.json"
        self.dashboard_path = f"/var/dashboards/{uuid.uuid4().hex}.json"
        self.stream_mock = io.BytesIO(uuid.uuid4().bytes)

    def test_collect_and_aggregate_telemetry(self):
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.system_health_aggregator.SystemHealthAggregator.collect_and_aggregate', return_value=expected_result) as mock_agg, \
             patch('skills.system_health_reporter.SystemHealthReporter.generate_health_report') as mock_rep:

            result = self.collector.collect_and_aggregate_telemetry(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list
            )

            mock_agg.assert_called_once_with(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list
            )
            mock_rep.assert_called()
            self.assertEqual(result, expected_result)

    def test_process_telemetry_stream(self):
        stream_path = f"/streams/{uuid.uuid4().hex}"
        expected_stream_result = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch('skills.system_health_aggregator.SystemHealthAggregator.process_stream', return_value=expected_stream_result) as mock_stream, \
             patch('skills.system_health_reporter.SystemHealthReporter.parse_stream_data') as mock_parse:

            result = self.collector.process_stream_telemetry(self.stream_mock, stream_path) if hasattr(self.collector, 'process_stream_telemetry') else self.collector.process_telemetry_stream(self.stream_mock, stream_path)

            mock_stream.assert_called_once_with(self.stream_mock, stream_path)
            mock_parse.assert_called_once()
            self.assertEqual(result, expected_stream_result)

    def test_export_comprehensive_report(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        export_path = f"/exports/{uuid.uuid4().hex}"
        expected_status = bool(random.getrandbits(1))

        with patch('skills.system_health_aggregator.SystemHealthAggregator.export_dashboard_file', return_value=expected_status) as mock_export_dash, \
             patch('skills.system_health_reporter.SystemHealthReporter.export_report_file') as mock_export_rep:

            status = self.collector.export_comprehensive_report(payload, export_path)

            mock_export_dash.assert_called_once_with(payload, export_path)
            mock_export_rep.assert_called()
            self.assertEqual(status, expected_status)

    def test_collect_and_process_telemetry(self):
        agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.system_health_aggregator.SystemHealthAggregator.collect_and_aggregate', return_value=agg_result) as mock_agg, \
             patch('skills.system_health_reporter.SystemHealthReporter.generate_health_report'), \
             patch('skills.system_health_reporter.SystemHealthReporter.export_report_file'), \
             patch('skills.system_health_aggregator.SystemHealthAggregator.export_dashboard_file', return_value=True), \
             patch('builtins.open', mock_open()) as mock_file:

            final_result = self.collector.collect_and_process_telemetry(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list,
                self.report_path,
                self.dashboard_path
            )

            mock_agg.assert_called_once()
            mock_file.assert_called_with(self.report_path, 'w')
            self.assertEqual(final_result, {self.module_name: agg_result})


if __name__ == '__main__':
    unittest.main()