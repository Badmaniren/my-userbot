import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string
import os

from skills.anomaly_audit_exporter import (
    AnomalyAuditExporter,
    AnomalyAuditExporterError
)

class TestAnomalyAuditExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(1.0, 100.0)
        self.output_path = f"/tmp/{uuid.uuid4().hex}_report.json"
        self.html_output_path = f"/tmp/{uuid.uuid4().hex}_report.html"

    @patch('skills.anomaly_audit_exporter.AnomalyAuditHub')
    @patch('skills.anomaly_audit_exporter.DigestExporter')
    def test_init_composition(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        instance = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        mock_audit_hub_cls.assert_called_once_with(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        mock_digest_exporter_cls.assert_called_once()
        self.assertIsNotNone(instance)

    @patch('skills.anomaly_audit_exporter.AnomalyAuditHub')
    @patch('skills.anomaly_audit_exporter.DigestExporter')
    def test_log_and_export_json(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        expected_return_path = f"/tmp/{uuid.uuid4().hex}.json"
        mock_exporter_instance.export_json_report.return_value = expected_return_path

        exporter = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        source = uuid.uuid4().hex
        severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(0, 1000)}

        result_path = exporter.log_and_export_json(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot,
            output_path=self.output_path
        )

        mock_hub_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        mock_exporter_instance.export_json_report.assert_called_once_with(self.output_path)
        self.assertEqual(result_path, expected_return_path)

    @patch('skills.anomaly_audit_exporter.AnomalyAuditHub')
    @patch('skills.anomaly_audit_exporter.DigestExporter')
    def test_run_audit_and_export_html(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        expected_html_path = f"/tmp/{uuid.uuid4().hex}.html"
        mock_exporter_instance.export_html_report.return_value = expected_html_path

        exporter = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        metric_name = uuid.uuid4().hex
        metric_value = random.uniform(0.0, 500.0)

        result_path = exporter.run_audit_and_export_html(
            metric_name=metric_name,
            value=metric_value,
            output_path=self.html_output_path
        )

        mock_hub_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=metric_value
        )
        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_html_report.assert_called_once_with(self.html_output_path)
        self.assertEqual(result_path, expected_html_path)

    @patch('skills.anomaly_audit_exporter.AnomalyAuditHub')
    @patch('skills.anomaly_audit_exporter.DigestExporter')
    def test_exception_handling_in_exporter(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        mock_hub_instance.generate_final_report.side_effect = Exception(uuid.uuid4().hex)

        exporter = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        with self.assertRaises(AnomalyAuditExporterError):
            exporter.run_audit_and_export_html(
                metric_name=uuid.uuid4().hex,
                value=random.random(),
                output_path=self.html_output_path
            )

    @patch('skills.anomaly_audit_exporter.AnomalyAuditHub')
    @patch('skills.anomaly_audit_exporter.DigestExporter')
    def test_stream_export_delegation(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_exporter_instance = mock_digest_exporter_cls.return_value
        stream_id = uuid.uuid4().hex
        expected_path = f"/tmp/{uuid.uuid4().hex}.json"
        mock_exporter_instance.export_stream_to_json.return_value = expected_path

        exporter = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        res = exporter.export_stream(stream_id=stream_id, output_path=self.output_path)

        mock_exporter_instance.export_stream_to_json.assert_called_once_with(stream_id, self.output_path)
        self.assertEqual(res, expected_path)

if __name__ == '__main__':
    unittest.main()