import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class TestSystemHealthTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.rand_module = f"module_{uuid.uuid4().hex[:8]}"
        self.rand_incident_key = f"inc_{uuid.uuid4().hex[:8]}"
        self.rand_incident_val = random.randint(1, 1000)
        self.rand_audit_key = f"audit_{uuid.uuid4().hex[:8]}"
        self.rand_audit_val = random.choice(string.ascii_letters)
        self.rand_metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        self.rand_metric_val = random.random() * 100
        self.rand_format = random.choice(["json", "yaml", "html", "xml"])
        self.rand_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.rand_stream_data = f"telemetry_stream_{uuid.uuid4().hex}".encode('utf-8')

    def test_composition_dependencies_exist(self):
        self.assertTrue(hasattr(self.collector, 'aggregator'), "Архитектурный сбой: модуль не содержит SystemHealthAggregator")
        self.assertTrue(hasattr(self.collector, 'reporter'), "Архитектурный сбой: модуль не содержит SystemHealthReporter")

    def test_collect_and_aggregate_telemetry(self):
        expected_aggregate_result = {
            f"agg_{uuid.uuid4().hex[:6]}": random.randint(1, 500),
            "status": random.choice(["HEALTHY", "DEGRADED", "CRITICAL"])
        }

        incident_data = {self.rand_incident_key: self.rand_incident_val}
        audit_summary = {self.rand_audit_key: self.rand_audit_val}
        metrics = {self.rand_metric_key: self.rand_metric_val}
        incidents_list = [f"inc_item_{uuid.uuid4().hex[:4]}" for _ in range(3)]
        patches_list = [f"patch_item_{uuid.uuid4().hex[:4]}" for _ in range(2)]

        with patch('skills.system_health_aggregator.SystemHealthAggregator.collect_and_aggregate') as mock_agg_collect, \
             patch('skills.system_health_reporter.SystemHealthReporter.generate_health_report') as mock_rep_gen:

            mock_agg_collect.return_value = expected_aggregate_result

            result = self.collector.collect_and_aggregate_telemetry(
                module_name=self.rand_module,
                incident_data=incident_data,
                audit_summary=audit_summary,
                metrics=metrics,
                dashboard_format=self.rand_format,
                incidents_list=incidents_list,
                patches_list=patches_list
            )

            mock_agg_collect.assert_called_once_with(
                self.rand_module, incident_data, audit_summary, metrics, self.rand_format, incidents_list, patches_list
            )
            mock_rep_gen.assert_called_once()
            self.assertEqual(result, expected_aggregate_result)

    def test_process_telemetry_stream(self):
        mock_stream = io.BytesIO(self.rand_stream_data)
        expected_parsed_data = {f"parsed_{uuid.uuid4().hex[:5]}": random.choice([True, False])}

        with patch('skills.system_health_aggregator.SystemHealthAggregator.process_stream') as mock_agg_stream, \
             patch('skills.system_health_reporter.SystemHealthReporter.parse_stream_data') as mock_rep_parse:

            mock_agg_stream.return_value = expected_parsed_data

            result = self.collector.process_telemetry_stream(mock_stream, self.rand_path)

            mock_agg_stream.assert_called_once_with(mock_stream, self.rand_path)
            mock_rep_parse.assert_called_once_with(mock_stream)
            self.assertEqual(result, expected_parsed_data)

    def test_export_comprehensive_report(self):
        payload = {f"payload_key_{uuid.uuid4().hex[:4]}": random.randint(100, 999)}
        expected_export_status = random.choice([True, False])

        with patch('skills.system_health_aggregator.SystemHealthAggregator.export_dashboard_file') as mock_agg_export, \
             patch('skills.system_health_reporter.SystemHealthReporter.export_report_file') as mock_rep_export:

            mock_agg_export.return_value = expected_export_status

            result = self.collector.export_comprehensive_report(payload, self.rand_path)

            mock_agg_export.assert_called_once_with(payload, self.rand_path)
            mock_rep_export.assert_called_once()
            self.assertEqual(result, expected_export_status)


if __name__ == '__main__':
    unittest.main()