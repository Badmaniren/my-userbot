import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class TestSystemHealthTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()

    def test_collect_and_aggregate_telemetry_success(self):
        module_name = uuid.uuid4().hex
        incident_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        audit_summary = uuid.uuid4().hex
        metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        dashboard_format = uuid.uuid4().hex
        incidents_list = [uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'collect_and_aggregate', return_value=expected_result) as mock_agg, \
             patch.object(self.collector.reporter, 'generate_health_report') as mock_rep:

            result = self.collector.collect_and_aggregate_telemetry(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )

            mock_agg.assert_called_once_with(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )
            mock_rep.assert_called_once_with(module_name)
            self.assertEqual(result, expected_result)

    def test_collect_and_aggregate_telemetry_with_type_error_handling(self):
        module_name = uuid.uuid4().hex
        incident_data = uuid.uuid4().hex
        audit_summary = uuid.uuid4().hex
        metrics = uuid.uuid4().hex
        dashboard_format = uuid.uuid4().hex
        incidents_list = []
        patches_list = []
        expected_result = uuid.uuid4().hex

        with patch.object(self.collector.aggregator, 'collect_and_aggregate', return_value=expected_result) as mock_agg, \
             patch.object(self.collector.reporter, 'generate_health_report', side_effect=[TypeError("Expected no args"), None]) as mock_rep:

            result = self.collector.collect_and_aggregate_telemetry(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )

            self.assertEqual(mock_rep.call_count, 2)
            mock_rep.assert_any_call(module_name)
            mock_rep.assert_any_call()
            self.assertEqual(result, expected_result)

    def test_process_telemetry_stream(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        path = uuid.uuid4().hex
        expected_stream_result = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch.object(self.collector.aggregator, 'process_stream', return_value=expected_stream_result) as mock_stream, \
             patch.object(self.collector.reporter, 'parse_stream_data') as mock_parse:

            result = self.collector.process_telemetry_stream(stream, path)

            mock_stream.assert_called_once_with(stream, path)
            mock_parse.assert_called_once()
            self.assertEqual(result, expected_stream_result)

    def test_export_comprehensive_report_success(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        path = uuid.uuid4().hex
        expected_status = uuid.uuid4().hex

        with patch.object(self.collector.aggregator, 'export_dashboard_file', return_value=expected_status) as mock_export, \
             patch.object(self.collector.reporter, 'export_report_file') as mock_rep_export:

            result = self.collector.export_comprehensive_report(payload, path)

            mock_export.assert_called_once_with(payload, path)
            mock_rep_export.assert_called_once_with(payload, path)
            self.assertEqual(result, expected_status)

    def test_export_comprehensive_report_with_type_error(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        path = uuid.uuid4().hex
        expected_status = uuid.uuid4().hex

        with patch.object(self.collector.aggregator, 'export_dashboard_file', return_value=expected_status) as mock_export, \
             patch.object(self.collector.reporter, 'export_report_file', side_effect=[TypeError("Expected no args"), None]) as mock_rep_export:

            result = self.collector.export_comprehensive_report(payload, path)

            self.assertEqual(mock_rep_export.call_count, 2)
            mock_rep_export.assert_any_call(payload, path)
            mock_rep_export.assert_any_call()
            self.assertEqual(result, expected_status)

    def test_collect_and_process_telemetry(self):
        module_name = uuid.uuid4().hex
        incident_data = {uuid.uuid4().hex: random.random()}
        audit_summary = uuid.uuid4().hex
        metrics = {uuid.uuid4().hex: random.randint(1, 50)}
        dashboard_format = uuid.uuid4().hex
        incidents_list = [uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]
        report_path = uuid.uuid4().hex
        dashboard_path = uuid.uuid4().hex
        agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector, 'collect_and_aggregate_telemetry', return_value=agg_result) as mock_collect, \
             patch.object(self.collector.reporter, 'export_report_file') as mock_rep_export, \
             patch.object(self.collector, 'export_comprehensive_report') as mock_export_comp, \
             patch('builtins.open', unittest.mock.mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:

            result = self.collector.collect_and_process_telemetry(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list,
                report_path,
                dashboard_path
            )

            mock_collect.assert_called_once_with(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )
            mock_rep_export.assert_called_once_with(agg_result, report_path)
            mock_export_comp.assert_called_once_with(agg_result, dashboard_path)
            mock_file.assert_called_once_with(report_path, 'w')
            mock_json_dump.assert_called_once()
            self.assertEqual(result, {module_name: agg_result})

    def test_process_stream_alias(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        path = uuid.uuid4().hex
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector, 'process_telemetry_stream', return_value=expected_result) as mock_process:
            result = self.collector.process_stream(stream, path)
            mock_process.assert_called_once_with(stream, path)
            self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()