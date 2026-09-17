import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import json
import os
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
        expected_agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'collect_and_aggregate', return_value=expected_agg_result) as mock_agg, \
             patch.object(self.collector.reporter, 'generate_health_report') as mock_report:

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
            mock_report.assert_called_once_with(module_name)
            self.assertEqual(result, expected_agg_result)

    def test_collect_and_aggregate_telemetry_fallback_reporter(self):
        module_name = uuid.uuid4().hex
        incident_data = {}
        audit_summary = uuid.uuid4().hex
        metrics = {}
        dashboard_format = uuid.uuid4().hex
        incidents_list = []
        patches_list = []
        expected_agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'collect_and_aggregate', return_value=expected_agg_result), \
             patch.object(self.collector.reporter, 'generate_health_report', side_effect=[TypeError, None]) as mock_report:

            result = self.collector.collect_and_aggregate_telemetry(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )

            self.assertEqual(mock_report.call_count, 2)
            mock_report.assert_any_call(module_name)
            mock_report.assert_any_call()
            self.assertEqual(result, expected_agg_result)

    def test_process_telemetry_stream_with_string(self):
        stream_content = uuid.uuid4().hex
        path = uuid.uuid4().hex
        expected_stream_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'process_stream', return_value=expected_stream_result) as mock_process, \
             patch.object(self.collector.reporter, 'parse_stream_data') as mock_parse:

            result = self.collector.process_telemetry_stream(stream_content, path)

            mock_process.assert_called_once()
            mock_parse.assert_called_once()
            self.assertEqual(result, expected_stream_result)

    def test_process_telemetry_stream_with_io(self):
        stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        path = uuid.uuid4().hex
        expected_stream_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'process_stream', return_value=expected_stream_result) as mock_process, \
             patch.object(self.collector.reporter, 'parse_stream_data', side_effect=[TypeError, TypeError, None]) as mock_parse:

            result = self.collector.process_telemetry_stream(stream, path)

            mock_process.assert_called_once_with(stream, path)
            self.assertEqual(mock_parse.call_count, 3)
            self.assertEqual(result, expected_stream_result)

    def test_export_comprehensive_report(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        path = uuid.uuid4().hex
        expected_status = uuid.uuid4().hex

        with patch.object(self.collector.aggregator, 'export_dashboard_file', return_value=expected_status) as mock_export_dash, \
             patch.object(self.collector.reporter, 'export_report_file', side_effect=[TypeError, None]) as mock_export_rep:

            status = self.collector.export_comprehensive_report(payload, path)

            mock_export_dash.assert_called_once_with(payload, path)
            self.assertEqual(mock_export_rep.call_count, 2)
            mock_export_rep.assert_any_call(payload, path)
            mock_export_rep.assert_any_call()
            self.assertEqual(status, expected_status)

    def test_collect_and_process_telemetry(self):
        module_name = uuid.uuid4().hex
        incident_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        audit_summary = uuid.uuid4().hex
        metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        dashboard_format = uuid.uuid4().hex
        incidents_list = [uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]
        report_path = f"{uuid.uuid4().hex}.json"
        dashboard_path = uuid.uuid4().hex
        expected_agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector, 'collect_and_aggregate_telemetry', return_value=expected_agg_result) as mock_collect_agg, \
             patch.object(self.collector.reporter, 'export_report_file', side_effect=[TypeError, None]) as mock_export_rep, \
             patch.object(self.collector, 'export_comprehensive_report') as mock_export_comp, \
             patch('builtins.open', unittest.mock.mock_open()) as mock_file:

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

            mock_collect_agg.assert_called_once_with(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )
            self.assertEqual(mock_export_rep.call_count, 2)
            mock_export_comp.assert_called_once_with(expected_agg_result, dashboard_path)
            mock_file.assert_called_once_with(report_path, 'w')
            self.assertEqual(result, {module_name: expected_agg_result})