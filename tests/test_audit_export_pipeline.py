import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.audit_export_pipeline import AuditExportPipeline, AuditExportPipelineError


class TestAuditExportPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)
        self.rand_output = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.rand_html_output = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.html"
        self.metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.metric_value = random.uniform(1.0, 1000.0)

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
        self.assertIsNotNone(pipeline)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_run_export_pipeline_json(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        expected_path = self.rand_output
        mock_exporter_instance.export_to_json.return_value = expected_path

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        pipeline.aggregate_metric(self.metric_name, self.metric_value)
        mock_hub_instance.aggregate_and_report.assert_called_once_with(self.metric_name, self.metric_value)

        result_path = pipeline.export_report(output_path=expected_path, format_type='json')

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_to_json.assert_called_once_with(expected_path)
        self.assertEqual(result_path, expected_path)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_run_export_pipeline_html(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        expected_path = self.rand_html_output
        mock_exporter_instance.export_to_html.return_value = expected_path

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        result_path = pipeline.export_report(output_path=expected_path, format_type='html')

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_to_html.assert_called_once_with(expected_path)
        self.assertEqual(result_path, expected_path)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_log_anomaly_in_pipeline(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value

        source = uuid.uuid4().hex
        severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry = {uuid.uuid4().hex: random.randint(0, 100)}

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        pipeline.log_pipeline_anomaly(source, severity, details, telemetry)

        mock_hub_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_pipeline_export_error_handling(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_exporter_instance = mock_digest_exporter_cls.return_value
        mock_exporter_instance.export_to_json.side_effect = Exception(uuid.uuid4().hex)

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        with self.assertRaises(AuditExportPipelineError):
            pipeline.export_report(output_path=self.rand_output, format_type='json')

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_unsupported_format_raises_error(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        bad_format = uuid.uuid4().hex

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        with self.assertRaises(AuditExportPipelineError):
            pipeline.export_report(output_path=self.rand_output, format_type=bad_format)


if __name__ == '__main__':
    unittest.main()