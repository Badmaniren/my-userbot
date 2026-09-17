import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import json
import io
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class TestSystemHealthTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.incident_data = {uuid.uuid4().hex: random.randint(1, 100)}
        self.audit_summary = f"audit_{uuid.uuid4().hex}"
        self.metrics = {uuid.uuid4().hex: random.random()}
        self.dashboard_format = random.choice(["json", "xml", "yaml", "html"])
        self.incidents_list = [uuid.uuid4().hex for _ in range(3)]
        self.patches_list = [uuid.uuid4().hex for _ in range(2)]
        self.report_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.dashboard_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.stream_data = f"stream_{uuid.uuid4().hex}".encode('utf-8')
        self.payload = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_collect_and_aggregate_telemetry_success(self):
        expected_agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'collect_and_aggregate', return_value=expected_agg_result) as mock_agg, \
             patch.object(self.collector.reporter, 'generate_health_report') as mock_rep:

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
            mock_rep.assert_called_once_with(self.module_name)
            self.assertEqual(result, expected_agg_result)

    def test_collect_and_aggregate_telemetry_type_error_fallback(self):
        expected_agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector.aggregator, 'collect_and_aggregate', return_value=expected_agg_result), \
             patch.object(self.collector.reporter, 'generate_health_report', side_effect=TypeError) as mock_rep:

            result = self.collector.collect_and_aggregate_telemetry(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list
            )

            self.assertEqual(mock_rep.call_count, 2)
            self.assertEqual(result, expected_agg_result)

    def test_process_telemetry_stream(self):
        stream_mock = io.BytesIO(self.stream_data)
        expected_stream_result = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch.object(self.collector.aggregator, 'process_stream', return_value=expected_stream_result) as mock_proc, \
             patch.object(self.collector.reporter, 'parse_stream_data') as mock_parse:

            result = self.collector.process_stream(stream_mock, self.dashboard_path)

            mock_proc.assert_called_once_with(stream_mock, self.dashboard_path)
            mock_parse.assert_called_once()
            self.assertEqual(result, expected_stream_result)

    def test_export_comprehensive_report(self):
        expected_export_status = random.choice([True, False])

        with patch.object(self.collector.aggregator, 'export_dashboard_file', return_value=expected_export_status) as mock_export, \
             patch.object(self.collector.reporter, 'export_report_file') as mock_rep_export:

            result = self.collector.export_comprehensive_report(self.payload, self.dashboard_path)

            mock_export.assert_called_once_with(self.payload, self.dashboard_path)
            mock_rep_export.assert_called_once_with(self.payload, self.dashboard_path)
            self.assertEqual(result, expected_export_status)

    def test_export_comprehensive_report_type_error_fallback(self):
        expected_export_status = random.choice([True, False])

        with patch.object(self.collector.aggregator, 'export_dashboard_file', return_value=expected_export_status), \
             patch.object(self.collector.reporter, 'export_report_file', side_effect=TypeError) as mock_rep_export:

            result = self.collector.export_comprehensive_report(self.payload, self.dashboard_path)

            self.assertEqual(mock_rep_export.call_count, 2)
            self.assertEqual(result, expected_export_status)

    def test_collect_and_process_telemetry(self):
        agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.collector, 'collect_and_aggregate_telemetry', return_value=agg_result) as mock_cat, \
             patch.object(self.collector.reporter, 'export_report_file') as mock_rep_export, \
             patch.object(self.collector, 'export_comprehensive_report') as mock_ecr, \
             patch('builtins.open', new_callable=unittest.mock.mock_open()) as mock_file:

            result = self.collector.collect_and_process_telemetry(
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

            mock_cat.assert_called_once()
            mock_rep_export.assert_called_once_with(agg_result, self.report_path)
            mock_ecr.assert_called_once_with(agg_result, self.dashboard_path)

            mock_file.assert_called_once_with(self.report_path, 'w')
            handle = mock_file.return_value.__enter__()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json, {self.module_name: agg_result, "status": "OK"})
            self.assertEqual(result, {self.module_name: agg_result})


if __name__ == '__main__':
    unittest.main()