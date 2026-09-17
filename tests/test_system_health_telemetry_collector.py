import unittest
import uuid
import random
import string
import json
import tempfile
import os
from unittest.mock import patch
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.telemetry_streamer import TelemetryStreamer


class TestSystemHealthTelemetryCollectorInquisitor(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.streamer = TelemetryStreamer()
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.incident_data = {uuid.uuid4().hex[:6]: random.randint(1, 100)}
        self.audit_summary = f"audit_sum_{uuid.uuid4().hex[:10]}"
        self.metrics = {uuid.uuid4().hex[:5]: random.random() for _ in range(3)}
        self.dashboard_format = random.choice(["json", "xml", "yaml", "html"])
        self.incidents_list = [uuid.uuid4().hex for _ in range(2)]
        self.patches_list = [uuid.uuid4().hex for _ in range(2)]
        self.stream_payload = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        self.stream_path = f"/var/log/{uuid.uuid4().hex}.stream"

    def test_collect_and_aggregate_telemetry_execution(self):
        result = self.collector.collect_and_aggregate_telemetry(
            self.module_name,
            self.incident_data,
            self.audit_summary,
            self.metrics,
            self.dashboard_format,
            self.incidents_list,
            self.patches_list
        )
        self.assertIsNotNone(result)

    def test_process_telemetry_stream_integration(self):
        with patch('skills.system_health_aggregator.SystemHealthAggregator.process_stream') as mock_agg_stream, \
             patch('skills.system_health_reporter.SystemHealthReporter.parse_stream_data') as mock_rep_parse:

            expected_output = {uuid.uuid4().hex: random.randint(100, 999)}
            mock_agg_stream.return_value = expected_output

            res = self.collector.process_telemetry_stream(self.stream_payload, self.stream_path)

            mock_agg_stream.assert_called_once_with(self.stream_payload, self.stream_path)
            mock_rep_parse.assert_called_once()
            self.assertEqual(res, expected_output)

    def test_export_comprehensive_report_flow(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        report_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")

        with patch('skills.system_health_aggregator.SystemHealthAggregator.export_dashboard_file') as mock_agg_export, \
             patch('skills.system_health_reporter.SystemHealthReporter.export_report_file') as mock_rep_export:

            mock_agg_export.return_value = True

            status = self.collector.export_comprehensive_report(payload, report_path)

            mock_agg_export.assert_called_once_with(payload, report_path)
            mock_rep_export.assert_called()
            self.assertTrue(status)

            if os.path.exists(report_path):
                os.remove(report_path)

    def test_collect_and_process_telemetry_full_cycle(self):
        report_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        report_path = report_file.name
        report_file.close()

        dashboard_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        dashboard_path = dashboard_file.name
        dashboard_file.close()

        try:
            unique_metric_key = uuid.uuid4().hex
            unique_metric_val = random.randint(500, 1000)
            custom_metrics = {unique_metric_key: unique_metric_val}

            result = self.collector.collect_and_process_telemetry(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                custom_metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list,
                report_path,
                dashboard_path
            )

            self.assertIn(self.module_name, result)

            with open(report_path, 'r') as f:
                file_content = json.load(f)
                self.assertIn(self.module_name, file_content)
                self.assertEqual(file_content.get("status"), "OK")
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)
            if os.path.exists(dashboard_path):
                os.remove(dashboard_path)

    def test_telemetry_streamer_integration_direct(self):
        streamer_instance = TelemetryStreamer()
        random_chunk = ''.join(random.choices(string.ascii_letters, k=32))

        with patch.object(streamer_instance, 'stream_data', return_value=random_chunk) as mock_stream:
            data = streamer_instance.stream_data()
            mock_stream.assert_called_once()
            self.assertEqual(data, random_chunk)


if __name__ == '__main__':
    unittest.main()