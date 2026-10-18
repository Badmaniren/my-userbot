import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.audit_exporter_pipeline import AuditExporterPipeline


class TestAuditExporterPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_output = f"/tmp/{uuid.uuid4().hex}.json"
        self.rand_html = f"/tmp/{uuid.uuid4().hex}.html"
        self.threshold = random.uniform(0.1, 99.9)

    def test_pipeline_initialization(self):
        with patch('skills.audit_exporter_pipeline.AnomalyAuditHub') as mock_hub_class, \
             patch('skills.audit_exporter_pipeline.DigestExporter') as mock_exporter_class:

            pipeline = AuditExporterPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.threshold
            )

            mock_hub_class.assert_called_once_with(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.threshold
            )
            mock_exporter_class.assert_called_once()
            self.assertIsNotNone(pipeline)

    def test_run_audit_and_export_json(self):
        rand_metric = f"metric_{uuid.uuid4().hex[:8]}"
        rand_value = random.randint(100, 9999)
        rand_return_path = f"/storage/{uuid.uuid4().hex}.json"

        with patch('skills.audit_exporter_pipeline.AnomalyAuditHub') as mock_hub_class, \
             patch('skills.audit_exporter_pipeline.DigestExporter') as mock_exporter_class:

            mock_hub_instance = mock_hub_class.return_value
            mock_hub_instance.generate_final_report.return_value = {
                "status": "secure",
                "id": uuid.uuid4().hex
            }

            mock_exporter_instance = mock_exporter_class.return_value
            mock_exporter_instance.export_json_report.return_value = rand_return_path

            pipeline = AuditExporterPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.threshold
            )

            result = pipeline.run_audit_and_export(output_path=self.rand_output, export_format="json")

            mock_hub_instance.aggregate_and_report.assert_called()
            mock_hub_instance.generate_final_report.assert_called_once()
            mock_exporter_instance.export_json_report.assert_called_once_with(self.rand_output)
            self.assertEqual(result, rand_return_path)

    def test_run_audit_and_export_html(self):
        rand_return_path = f"/storage/{uuid.uuid4().hex}.html"

        with patch('skills.audit_exporter_pipeline.AnomalyAuditHub') as mock_hub_class, \
             patch('skills.audit_exporter_pipeline.DigestExporter') as mock_exporter_class:

            mock_hub_instance = mock_hub_class.return_value
            mock_exporter_instance = mock_exporter_class.return_value
            mock_exporter_instance.export_html_report.return_value = rand_return_path

            pipeline = AuditExporterPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.threshold
            )

            result = pipeline.run_audit_and_export(output_path=self.rand_output, export_format="html")

            mock_exporter_instance.export_html_report.assert_called_once_with(self.rand_output)
            self.assertEqual(result, rand_return_path)

    def test_log_and_track_anomaly(self):
        rand_source = f"source_{uuid.uuid4().hex[:6]}"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = {"info": uuid.uuid4().hex}
        rand_telemetry = {"cpu": random.random()}

        with patch('skills.audit_exporter_pipeline.AnomalyAuditHub') as mock_hub_class, \
             patch('skills.audit_exporter_pipeline.DigestExporter'):

            mock_hub_instance = mock_hub_class.return_value

            pipeline = AuditExporterPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.threshold
            )

            pipeline.log_external_anomaly(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )

            mock_hub_instance.log_anomaly.assert_called_once_with(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )


if __name__ == '__main__':
    unittest.main()