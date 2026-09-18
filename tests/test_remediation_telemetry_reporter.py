import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.remediation_telemetry_reporter import RemediationTelemetryReporter


class TestRemediationTelemetryReporter(unittest.TestCase):

    def setUp(self):
        self.reporter = RemediationTelemetryReporter()
        self.pipeline_id = str(uuid.uuid4())
        self.module_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_value = random.uniform(0.1, 100.0)
        self.report_path = f"/tmp/{uuid.uuid4().hex}.json"

    def test_generate_comprehensive_report_composition(self):
        incident_data = {"id": uuid.uuid4().hex, "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])}
        audit_summary = {"status": "PASSED", "score": random.randint(50, 100)}
        metrics = {self.metric_name: self.metric_value}
        dashboard_format = random.choice(["json", "html", "pdf"])
        incidents_list = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
        patches_list = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

        mock_telemetry_result = {
            "telemetry_id": uuid.uuid4().hex,
            "status": "aggregated"
        }
        mock_export_result = {
            "path": self.report_path,
            "exported": True
        }

        with patch('skills.remediation_telemetry_reporter.SystemHealthTelemetryCollector') as MockHealthCollector, \
             patch('skills.remediation_telemetry_reporter.VulnerabilityRemediationMetricsCollector') as MockMetricsCollector:

            health_instance = MockHealthCollector.return_value
            health_instance.collect_and_aggregate_telemetry.return_value = mock_telemetry_result
            health_instance.export_comprehensive_report.return_value = mock_export_result

            metrics_instance = MockMetricsCollector.return_value
            metrics_instance.collect_metric.return_value = True
            metrics_instance.aggregate_pipeline_metrics.return_value = {self.pipeline_id: self.metric_value}

            result = self.reporter.generate_remediation_telemetry_report(
                pipeline_id=self.pipeline_id,
                module_name=self.module_name,
                incident_data=incident_data,
                audit_summary=audit_summary,
                metrics=metrics,
                dashboard_format=dashboard_format,
                incidents_list=incidents_list,
                patches_list=patches_list,
                report_path=self.report_path
            )

            health_instance.collect_and_aggregate_telemetry.assert_called_once_with(
                self.module_name, incident_data, audit_summary, metrics, dashboard_format, incidents_list, patches_list
            )
            health_instance.export_comprehensive_report.assert_called_once()
            metrics_instance.collect_metric.assert_called()

            self.assertIn("report", result)
            self.assertIn("telemetry", result)
            self.assertEqual(result["telemetry"], mock_telemetry_result)

    def test_process_stream_with_random_payload(self):
        stream_content = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        with patch('skills.remediation_telemetry_reporter.SystemHealthTelemetryCollector') as MockHealthCollector:
            health_instance = MockHealthCollector.return_value
            health_instance.process_telemetry_stream.return_value = True

            res = self.reporter.process_stream_data(mock_stream, self.report_path)

            health_instance.process_telemetry_stream.assert_called_once_with(mock_stream, self.report_path)
            self.assertTrue(res)

    def test_handle_telemetry_error_propagation(self):
        error_context = {"error_code": random.randint(1000, 9999), "message": uuid.uuid4().hex}

        with patch('skills.remediation_telemetry_reporter.VulnerabilityRemediationMetricsCollector') as MockMetricsCollector:
            metrics_instance = MockMetricsCollector.return_value
            metrics_instance.handle_telemetry_error_sync.return_value = {"handled": True, "pipeline": self.pipeline_id}

            res = self.reporter.report_telemetry_error(self.pipeline_id, error_context)

            metrics_instance.handle_telemetry_error_sync.assert_called_once_with(self.pipeline_id, error_context)
            self.assertTrue(res["handled"])
            self.assertEqual(res["pipeline"], self.pipeline_id)

    def test_export_metrics_stream_delegation(self):
        stream_identifier = uuid.uuid4().hex
        mock_exported_data = io.BytesIO(b"random_metric_stream_bytes")

        with patch('skills.remediation_telemetry_reporter.VulnerabilityRemediationMetricsCollector') as MockMetricsCollector:
            metrics_instance = MockMetricsCollector.return_value
            metrics_instance.export_metrics_stream.return_value = mock_exported_data

            result_stream = self.reporter.export_metrics(stream_identifier)

            metrics_instance.export_metrics_stream.assert_called_once_with(stream_identifier)
            self.assertEqual(result_stream, mock_exported_data)


if __name__ == '__main__':
    unittest.main()