import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.audit_export_pipeline import AuditExportPipeline, AuditExportPipelineError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestAuditExportPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo_{uuid.uuid4().hex[:8]}"
        self.rand_log = f"/log_{uuid.uuid4().hex[:8]}.log"
        self.rand_threshold = random.uniform(0.1, 0.9)
        self.rand_output = f"/output_{uuid.uuid4().hex[:8]}.json"

        self.rand_source = f"source_{uuid.uuid4().hex[:6]}"
        self.rand_severity = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        self.rand_details = f"details_{uuid.uuid4().hex[:10]}"
        self.rand_telemetry = {"cpu": random.randint(1, 100), "mem": random.randint(1, 100)}

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
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
        self.assertIsNotNone(pipeline.audit_hub)
        self.assertIsNotNone(pipeline.exporter)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_log_and_export_success(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        expected_export_path = f"/exported_{uuid.uuid4().hex[:6]}.json"
        mock_exporter_instance.export_json_report.return_value = expected_export_path

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        result_path = pipeline.log_and_export(
            source=self.rand_source,
            severity=self.rand_severity,
            details=self.rand_details,
            telemetry_snapshot=self.rand_telemetry,
            output_path=self.rand_output
        )

        mock_hub_instance.log_anomaly.assert_called_once_with(
            source=self.rand_source,
            severity=self.rand_severity,
            details=self.rand_details,
            telemetry_snapshot=self.rand_telemetry
        )
        mock_exporter_instance.export_json_report.assert_called_once_with(self.rand_output)
        self.assertEqual(result_path, expected_export_path)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_log_and_export_handles_exception(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        rand_error_msg = f"err_{uuid.uuid4().hex[:8]}"
        mock_hub_instance.log_anomaly.side_effect = Exception(rand_error_msg)

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        with self.assertRaises(AuditExportPipelineError) as ctx:
            pipeline.log_and_export(
                source=self.rand_source,
                severity=self.rand_severity,
                details=self.rand_details,
                telemetry_snapshot=self.rand_telemetry,
                output_path=self.rand_output
            )

        self.assertIn(rand_error_msg, str(ctx.exception))

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_generate_report_and_export_html(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        rand_html_path = f"/report_{uuid.uuid4().hex[:6]}.html"
        mock_exporter_instance.export_html_report.return_value = rand_html_path

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        res_path = pipeline.export_html(output_path=rand_html_path)

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_html_report.assert_called_once_with(rand_html_path)
        self.assertEqual(res_path, rand_html_path)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_aggregate_and_report_proxy(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        rand_metric = f"metric_{uuid.uuid4().hex[:5]}"
        rand_val = random.uniform(10.0, 100.0)
        rand_response = f"resp_{uuid.uuid4().hex[:6]}"
        mock_hub_instance.aggregate_and_report.return_value = rand_response

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        res = pipeline.aggregate_metric(metric_name=rand_metric, value=rand_val)

        mock_hub_instance.aggregate_and_report.assert_called_once_with(rand_metric, rand_val)
        self.assertEqual(res, rand_response)


if __name__ == '__main__':
    unittest.main()