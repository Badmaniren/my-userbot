import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.digest_audit_pipeline import DigestAuditPipeline, DigestAuditPipelineError

class TestDigestAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.output_path = f"/reports/{uuid.uuid4().hex}.json"
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(10.0, 100.0), 2)

    def test_pipeline_initialization(self):
        with patch('skills.digest_audit_pipeline.AnomalyAuditHub') as MockHub, \
             patch('skills.digest_audit_pipeline.DigestExporter') as MockExporter:

            pipeline = DigestAuditPipeline(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            MockHub.assert_called_once_with(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )
            MockExporter.assert_called_once()
            self.assertIsNotNone(pipeline)

    def test_run_audit_and_export_success(self):
        source = f"src_{uuid.uuid4().hex[:4]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"details_{uuid.uuid4().hex}"
        telemetry = {"cpu": random.randint(1, 100)}
        format_type = random.choice(["json", "html"])

        with patch('skills.digest_audit_pipeline.AnomalyAuditHub') as MockHubClass, \
             patch('skills.digest_audit_pipeline.DigestExporter') as MockExporterClass:

            mock_hub = MockHubClass.return_value
            mock_exporter = MockExporterClass.return_value

            expected_result = f"/output/{uuid.uuid4().hex}.{format_type}"
            if format_type == "json":
                mock_exporter.export_to_json.return_value = expected_result
            else:
                mock_exporter.export_to_html.return_value = expected_result

            pipeline = DigestAuditPipeline(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            result = pipeline.run_audit_and_export(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry,
                metric_name=self.metric_name,
                metric_value=self.metric_value,
                output_path=self.output_path,
                format_type=format_type
            )

            mock_hub.log_anomaly.assert_called_once_with(source, severity, details, telemetry)
            mock_hub.aggregate_and_report.assert_called_once_with(self.metric_name, self.metric_value)
            mock_hub.generate_final_report.assert_called_once()

            if format_type == "json":
                mock_exporter.export_to_json.assert_called_once_with(self.output_path)
            else:
                mock_exporter.export_to_html.assert_called_once_with(self.output_path)

            self.assertEqual(result, expected_result)

    def test_run_audit_and_export_invalid_format(self):
        invalid_format = f"pdf_{uuid.uuid4().hex[:4]}"

        with patch('skills.digest_audit_pipeline.AnomalyAuditHub'), \
             patch('skills.digest_audit_pipeline.DigestExporter'):

            pipeline = DigestAuditPipeline(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            with self.assertRaises(DigestAuditPipelineError) as ctx:
                pipeline.run_audit_and_export(
                    source=f"src_{uuid.uuid4().hex}",
                    severity="HIGH",
                    details=f"det_{uuid.uuid4().hex}",
                    telemetry_snapshot={},
                    metric_name=self.metric_name,
                    metric_value=self.metric_value,
                    output_path=self.output_path,
                    format_type=invalid_format
                )

            self.assertIn(invalid_format, str(ctx.exception))

    def test_run_audit_and_export_exporter_exception(self):
        format_type = "json"

        with patch('skills.digest_audit_pipeline.AnomalyAuditHub') as MockHubClass, \
             patch('skills.digest_audit_pipeline.DigestExporter') as MockExporterClass, \
             patch('skills.digest_audit_pipeline.DigestExporterError', Exception):

            mock_exporter = MockExporterClass.return_value
            mock_exporter.export_to_json.side_effect = Exception(f"Export failed {uuid.uuid4().hex}")

            pipeline = DigestAuditPipeline(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            with self.assertRaises(DigestAuditPipelineError):
                pipeline.run_audit_and_export(
                    source=f"src_{uuid.uuid4().hex}",
                    severity="LOW",
                    details=f"det_{uuid.uuid4().hex}",
                    telemetry_snapshot={},
                    metric_name=self.metric_name,
                    metric_value=self.metric_value,
                    output_path=self.output_path,
                    format_type=format_type
                )

if __name__ == '__main__':
    unittest.main()