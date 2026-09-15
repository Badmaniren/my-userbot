import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.system_health_audit_pipeline import SystemHealthAuditPipeline


class TestSystemHealthAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.module_name = ''.join(random.choices(string.ascii_lowercase, k=10)) + '_' + uuid.uuid4().hex[:6]
        self.incident_data = {uuid.uuid4().hex[:6]: random.randint(1, 100) for _ in range(3)}
        self.audit_summary = {uuid.uuid4().hex[:6]: uuid.uuid4().hex for _ in range(2)}
        self.metrics = {uuid.uuid4().hex[:6]: random.random() for _ in range(4)}
        self.dashboard_format = random.choice(['json', 'yaml', 'html', 'xml'])
        self.incidents_list = [uuid.uuid4().hex for _ in range(3)]
        self.patches_list = [uuid.uuid4().hex for _ in range(2)]
        self.report_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.dashboard_path = f"/tmp/{uuid.uuid4().hex}.dashboard"
        
        self.stream_data = b" ".join([uuid.uuid4().bytes for _ in range(5)])
        self.stream_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.payload = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_pipeline_initialization(self):
        pipeline = SystemHealthAuditPipeline()
        self.assertIsNotNone(pipeline)
        self.assertIsNotNone(pipeline.telemetry_collector)
        self.assertIsNotNone(pipeline.aggregator)

    def test_run_audit_pipeline_success(self):
        expected_telemetry_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_aggregate_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.system_health_telemetry_collector.SystemHealthTelemetryCollector.collect_and_process_telemetry') as mock_telemetry, \
             patch('skills.system_health_aggregator.SystemHealthAggregator.collect_and_aggregate') as mock_aggregator:
            
            mock_telemetry.return_value = expected_telemetry_result
            mock_aggregator.return_value = expected_aggregate_result

            pipeline = SystemHealthAuditPipeline()
            result = pipeline.run_audit_pipeline(
                module_name=self.module_name,
                incident_data=self.incident_data,
                audit_summary=self.audit_summary,
                metrics=self.metrics,
                dashboard_format=self.dashboard_format,
                incidents_list=self.incidents_list,
                patches_list=self.patches_list,
                report_path=self.report_path,
                dashboard_path=self.dashboard_path
            )

            mock_telemetry.assert_called_once_with(
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
            mock_aggregator.assert_called_once_with(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list
            )
            
            self.assertIn("telemetry", result)
            self.assertIn("aggregation", result)
            self.assertEqual(result["telemetry"], expected_telemetry_result)
            self.assertEqual(result["aggregation"], expected_aggregate_result)

    def test_process_audit_stream_pipeline(self):
        mock_stream = io.BytesIO(self.stream_data)
        expected_stream_result = uuid.uuid4().hex

        with patch('skills.system_health_telemetry_collector.SystemHealthTelemetryCollector.process_telemetry_stream') as mock_telemetry_stream, \
             patch('skills.system_health_aggregator.SystemHealthAggregator.process_stream') as mock_aggregator_stream:

            mock_telemetry_stream.return_value = expected_stream_result
            mock_aggregator_stream.return_value = expected_stream_result

            pipeline = SystemHealthAuditPipeline()
            res_telemetry, res_aggregator = pipeline.process_audit_stream(mock_stream, self.stream_path)

            mock_telemetry_stream.assert_called_once_with(mock_stream, self.stream_path)
            mock_aggregator_stream.assert_called_once_with(mock_stream, self.stream_path)

            self.assertEqual(res_telemetry, expected_stream_result)
            self.assertEqual(res_aggregator, expected_stream_result)

    def test_export_and_save_pipeline_artifacts(self):
        with patch('skills.system_health_telemetry_collector.SystemHealthTelemetryCollector.export_comprehensive_report') as mock_export_report, \
             patch('skills.system_health_aggregator.SystemHealthAggregator.save_dashboard_file') as mock_save_dash:

            pipeline = SystemHealthAuditPipeline()
            pipeline.export_and_save_pipeline_artifacts(self.payload, self.report_path, self.dashboard_path)

            mock_export_report.assert_called_once_with(self.payload, self.report_path)
            mock_save_dash.assert_called_once_with(self.payload, self.dashboard_path)


if __name__ == '__main__':
    unittest.main()