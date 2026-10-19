import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.audit_pipeline_exporter import AuditPipelineExporter, AuditPipelineExporterError
from skills.anomaly_pipeline import AnomalyPipeline
from skills.digest_exporter import DigestExporter


class TestAuditPipelineExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        with patch('skills.audit_pipeline_exporter.AnomalyPipeline', spec=AnomalyPipeline) as mock_pipeline_cls, \
             patch('skills.audit_pipeline_exporter.DigestExporter', spec=DigestExporter) as mock_exporter_cls:

            self.mock_pipeline_instance = mock_pipeline_cls.return_value
            self.mock_exporter_instance = mock_exporter_cls.return_value

            self.exporter = AuditPipelineExporter(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_initialization_composes_skills(self):
        self.assertEqual(self.exporter.repo_path, self.repo_path)
        self.assertEqual(self.exporter.log_path, self.log_path)
        self.assertEqual(self.exporter.threshold, self.threshold)
        self.assertIsInstance(self.exporter.pipeline, AnomalyPipeline)
        self.assertIsInstance(self.exporter.exporter, DigestExporter)

    def test_run_audit_and_export_json_success(self):
        execution_id = uuid.uuid4().hex
        metrics_key = f"metric_{uuid.uuid4().hex[:6]}"
        metrics_val = random.randint(10, 1000)
        raw_metrics = {metrics_key: metrics_val}

        expected_pipeline_result = {
            "execution_id": execution_id,
            "status": "completed",
            "anomalies_found": random.randint(0, 5)
        }
        self.mock_pipeline_instance.run_end_to_end.return_value = expected_pipeline_result

        output_json_path = f"/tmp/export_{uuid.uuid4().hex}.json"
        expected_json_str = f'{{"execution_id": "{execution_id}", "status": "success"}}'
        self.mock_exporter_instance.export_json_report.return_value = expected_json_str

        result = self.exporter.run_audit_and_export_json(execution_id, raw_metrics, output_json_path)

        self.mock_pipeline_instance.run_end_to_end.assert_called_once_with(execution_id, raw_metrics)
        self.mock_exporter_instance.export_json_report.assert_called_once_with(output_json_path)
        self.assertEqual(result, expected_json_str)

    def test_run_audit_and_export_html_success(self):
        execution_id = uuid.uuid4().hex
        raw_metrics = {uuid.uuid4().hex: random.random()}

        output_html_path = f"/tmp/report_{uuid.uuid4().hex}.html"
        expected_html_str = f"<html><body>Report {execution_id}</body></html>"
        self.mock_exporter_instance.export_html_report.return_value = expected_html_str

        result = self.exporter.run_audit_and_export_html(execution_id, raw_metrics, output_html_path)

        self.mock_pipeline_instance.run_end_to_end.assert_called_once_with(execution_id, raw_metrics)
        self.mock_exporter_instance.export_html_report.assert_called_once_with(output_html_path)
        self.assertEqual(result, expected_html_str)

    def test_run_audit_pipeline_failure_raises_custom_error(self):
        execution_id = uuid.uuid4().hex
        raw_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        output_path = f"/tmp/{uuid.uuid4().hex}.json"

        error_message = f"Pipeline failure {uuid.uuid4().hex}"
        self.mock_pipeline_instance.run_end_to_end.side_effect = Exception(error_message)

        with self.assertRaises(AuditPipelineExporterError) as ctx:
            self.exporter.run_audit_and_export_json(execution_id, raw_metrics, output_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_export_digest_failure_raises_custom_error(self):
        execution_id = uuid.uuid4().hex
        raw_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        output_path = f"/tmp/{uuid.uuid4().hex}.json"

        self.mock_pipeline_instance.run_end_to_end.return_value = {"status": "ok"}
        exporter_error_msg = f"Export failed {uuid.uuid4().hex}"
        self.mock_exporter_instance.export_json_report.side_effect = Exception(exporter_error_msg)

        with self.assertRaises(AuditPipelineExporterError) as ctx:
            self.exporter.run_audit_and_export_json(execution_id, raw_metrics, output_path)

        self.assertIn(exporter_error_msg, str(ctx.exception))

    def test_stream_export_execution(self):
        stream_id = uuid.uuid4().hex
        output_path = f"/tmp/stream_{uuid.uuid4().hex}.json"
        expected_stream_result = f'{{"stream_id": "{stream_id}", "exported": true}}'

        self.mock_exporter_instance.export_stream_to_json.return_value = expected_stream_result

        result = self.exporter.export_pipeline_stream(stream_id, output_path)

        self.mock_exporter_instance.export_stream_to_json.assert_called_once_with(stream_id, output_path)
        self.assertEqual(result, expected_stream_result)


if __name__ == '__main__':
    unittest.main()