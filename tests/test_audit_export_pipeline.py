import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.audit_export_pipeline import (
    AuditExportPipeline,
    AuditExportPipelineError
)

class TestAuditExportPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/var/repo_{uuid.uuid4().hex[:8]}"
        self.log_path_val = f"/var/log_{uuid.uuid4().hex[:8]}.log"
        self.threshold_val = round(random.uniform(1.0, 10.0), 2)
        self.output_path_val = f"/tmp/report_{uuid.uuid4().hex[:8]}.json"
        self.metric_name_val = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value_val = round(random.uniform(50.0, 500.0), 2)

        self.source_val = f"source_{uuid.uuid4().hex[:6]}"
        self.severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details_val = {"info": uuid.uuid4().hex}
        self.telemetry_snapshot_val = {"cpu": random.randint(10, 99)}

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_pipeline_initialization_and_logging(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        pipeline = AuditExportPipeline(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )

        mock_anomaly_hub_cls.assert_called_once_with(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )
        mock_digest_exporter_cls.assert_called_once()
        self.assertEqual(pipeline.hub, mock_hub_instance)
        self.assertEqual(pipeline.exporter, mock_exporter_instance)

        pipeline.log_anomaly_in_pipeline(
            source=self.source_val,
            severity=self.severity_val,
            details=self.details_val,
            telemetry_snapshot=self.telemetry_snapshot_val
        )

        mock_hub_instance.log_anomaly.assert_called_once_with(
            source=self.source_val,
            severity=self.severity_val,
            details=self.details_val,
            telemetry_snapshot=self.telemetry_snapshot_val
        )

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_aggregate_and_report_delegation(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        expected_aggregate_result = f"agg_{uuid.uuid4().hex[:8]}"
        mock_hub_instance.aggregate_and_report.return_value = expected_aggregate_result

        pipeline = AuditExportPipeline(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )

        res = pipeline.aggregate_pipeline_metric(
            metric_name=self.metric_name_val,
            value=self.metric_value_val
        )

        mock_hub_instance.aggregate_and_report.assert_called_once_with(
            metric_name=self.metric_name_val,
            value=self.metric_value_val
        )
        self.assertEqual(res, expected_aggregate_result)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_export_pipeline_json_report(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_exporter_instance = mock_digest_exporter_cls.return_value
        expected_export_path = f"/reports/{uuid.uuid4().hex[:8]}.json"
        mock_exporter_instance.export_json_report.return_value = expected_export_path

        pipeline = AuditExportPipeline(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )

        result_path = pipeline.export_pipeline_report(output_path=self.output_path_val)

        mock_exporter_instance.export_json_report.assert_called_once_with(self.output_path_val)
        self.assertEqual(result_path, expected_export_path)

    @patch('skills.audit_export_pipeline.AnomalyAuditHub')
    @patch('skills.audit_export_pipeline.DigestExporter')
    def test_pipeline_exception_handling(self, mock_digest_exporter_cls, mock_anomaly_hub_cls):
        mock_hub_instance = mock_anomaly_hub_cls.return_value
        err_msg = f"critical_failure_{uuid.uuid4().hex[:6]}"
        mock_hub_instance.log_anomaly.side_effect = Exception(err_msg)

        pipeline = AuditExportPipeline(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )

        with self.assertRaises(AuditExportPipelineError) as ctx:
            pipeline.log_anomaly_in_pipeline(
                source=self.source_val,
                severity=self.severity_val,
                details=self.details_val,
                telemetry_snapshot=self.telemetry_snapshot_val
            )

        self.assertIn(err_msg, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()