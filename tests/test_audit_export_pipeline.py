import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.audit_export_pipeline import AuditExportPipeline, AuditExportPipelineError


class TestAuditExportPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo_{uuid.uuid4().hex[:8]}"
        self.rand_log = f"/log_{uuid.uuid4().hex[:8]}.log"
        self.rand_threshold = round(random.uniform(0.1, 9.9), 2)
        self.rand_output = f"/out_{uuid.uuid4().hex[:8]}.json"

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_pipeline_initialization(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        mock_anomaly_hub_cls.assert_called_once_with(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )
        mock_digest_exporter_cls.assert_called_once()
        self.assertIsNotNone(pipeline.hub)
        self.assertIsNotNone(pipeline.exporter)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_run_export_json_success(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        rand_report_content = f"report_data_{uuid.uuid4().hex}"
        mock_hub_instance.generate_final_report.return_value = rand_report_content

        rand_file_result = f"/path/to/{uuid.uuid4().hex}.json"
        mock_exporter_instance.export_to_json.return_value = rand_file_result

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        result = pipeline.run_export(output_path=self.rand_output, format_type='json')

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_to_json.assert_called_once_with(self.rand_output)
        self.assertEqual(result, rand_file_result)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_run_export_html_success(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        rand_file_result = f"/path/to/{uuid.uuid4().hex}.html"
        mock_exporter_instance.export_to_html.return_value = rand_file_result

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        result = pipeline.run_export(output_path=self.rand_output, format_type='html')

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_to_html.assert_called_once_with(self.rand_output)
        self.assertEqual(result, rand_file_result)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_run_export_unsupported_format(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        rand_bad_format = ''.join(random.choices(string.ascii_lowercase, k=5))
        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        with self.assertRaises((ValueError, AuditExportPipelineError)):
            pipeline.run_export(output_path=self.rand_output, format_type=rand_bad_format)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_log_and_aggregate_integration(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value

        rand_source = f"src_{uuid.uuid4().hex[:6]}"
        rand_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        rand_details = f"details_{uuid.uuid4().hex}"
        rand_snapshot = {uuid.uuid4().hex: uuid.uuid4().hex}

        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_value = random.randint(10, 1000)

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        pipeline.record_anomaly(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )

        mock_hub_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )

        pipeline.aggregate_metric(metric_name=rand_metric, value=rand_value)
        mock_hub_instance.aggregate_and_report.assert_called_once_with(
            metric_name=rand_metric,
            value=rand_value
        )