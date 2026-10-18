import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.audit_export_pipeline import AuditExportPipeline, AuditExportPipelineError

class TestAuditExportPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.rand_log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_output_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.rand_html_path = f"/tmp/{uuid.uuid4().hex}.html"
        self.rand_metric = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_value = random.uniform(1.0, 100.0)
        self.rand_threshold = random.uniform(0.1, 0.9)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_pipeline_initialization(self, mock_digest_exporter_cls, mock_anomaly_audit_hub_cls):
        hub_instance = mock_anomaly_audit_hub_cls.return_value
        exporter_instance = mock_digest_exporter_cls.return_value

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_path,
            threshold=self.rand_threshold
        )

        mock_anomaly_audit_hub_cls.assert_called_once_with(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_path,
            threshold=self.rand_threshold
        )
        mock_digest_exporter_cls.assert_called_once()
        self.assertEqual(pipeline.hub, hub_instance)
        self.assertEqual(pipeline.exporter, exporter_instance)

    @patch('skills.audit_export_pipeline.DigestExporter')
    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    def test_run_audit_and_export_json(self, mock_anomaly_audit_hub_cls, mock_digest_exporter_cls):
        hub_instance = mock_anomaly_audit_hub_cls.return_value
        exporter_instance = mock_digest_exporter_cls.return_value

        expected_report_path = f"/tmp/{uuid.uuid4().hex}.json"
        exporter_instance.export_json_report.return_value = expected_report_path

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_path,
            threshold=self.rand_threshold
        )

        result_path = pipeline.run_audit_and_export_json(self.rand_output_path)

        hub_instance.generate_final_report.assert_called_once()
        exporter_instance.export_json_report.assert_called_once_with(self.rand_output_path)
        self.assertEqual(result_path, expected_report_path)

    @patch('skills.audit_export_pipeline.DigestExporter')
    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    def test_run_audit_and_export_html(self, mock_anomaly_audit_hub_cls, mock_digest_exporter_cls):
        hub_instance = mock_anomaly_audit_hub_cls.return_value
        exporter_instance = mock_digest_exporter_cls.return_value

        expected_html_path = f"/tmp/{uuid.uuid4().hex}.html"
        exporter_instance.export_html_report.return_value = expected_html_path

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_path,
            threshold=self.rand_threshold
        )

        result_path = pipeline.run_audit_and_export_html(self.rand_html_path)

        hub_instance.generate_final_report.assert_called_once()
        exporter_instance.export_html_report.assert_called_once_with(self.rand_html_path)
        self.assertEqual(result_path, expected_html_path)

    @patch('skills.audit_export_pipeline.DigestExporter')
    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    def test_log_and_aggregate(self, mock_anomaly_audit_hub_cls, mock_digest_exporter_cls):
        hub_instance = mock_anomaly_audit_hub_cls.return_value

        source = uuid.uuid4().hex
        severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details = {'info': uuid.uuid4().hex}
        telemetry = {'cpu': random.randint(1, 100)}

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_path,
            threshold=self.rand_threshold
        )

        pipeline.log_and_aggregate_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry,
            metric_name=self.rand_metric,
            value=self.rand_value
        )

        hub_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )
        hub_instance.aggregate_and_report.assert_called_once_with(
            metric_name=self.rand_metric,
            value=self.rand_value
        )

    @patch('skills.audit_export_pipeline.DigestExporter')
    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    def test_export_pipeline_exception_handling(self, mock_anomaly_audit_hub_cls, mock_digest_exporter_cls):
        hub_instance = mock_anomaly_audit_hub_cls.return_value
        hub_instance.generate_final_report.side_effect = Exception(uuid.uuid4().hex)

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_path,
            threshold=self.rand_threshold
        )

        with self.assertRaises(AuditExportPipelineError):
            pipeline.run_audit_and_export_json(self.rand_output_path)

if __name__ == '__main__':
    unittest.main()