import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.audit_exporter import AuditExporter, AuditExporterError


class TestAuditExporter(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 10.0)

        self.mock_audit_hub = MagicMock()
        self.mock_digest_exporter = MagicMock()

    def test_init_creates_default_components(self):
        with patch("skills.audit_exporter.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.audit_exporter.DigestExporter") as mock_exporter_cls:

            exporter = AuditExporter(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            mock_hub_cls.assert_called_once_with(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )
            mock_exporter_cls.assert_called_once()

    def test_init_with_injected_components(self):
        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )
        self.assertEqual(exporter.audit_hub, self.mock_audit_hub)
        self.assertEqual(exporter.digest_exporter, self.mock_digest_exporter)

    def test_log_anomaly_delegates_to_hub(self):
        source = f"source_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"details_{uuid.uuid4().hex}"
        snapshot = {"cpu": random.randint(10, 100)}

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        exporter.log_anomaly(source, severity, details, telemetry_snapshot=snapshot)

        self.mock_audit_hub.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=snapshot
        )

    def test_generate_final_report_delegates_to_hub(self):
        expected_report = f"report_{uuid.uuid4().hex}"
        self.mock_audit_hub.generate_final_report.return_value = expected_report

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        result = exporter.generate_final_report()

        self.assertEqual(result, expected_report)
        self.mock_audit_hub.generate_final_report.assert_called_once()

    def test_export_json_report_success(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        expected_result = f"path_json_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_json_report.return_value = expected_result

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        result = exporter.export_json_report(output_path)

        self.assertEqual(result, expected_result)
        self.mock_digest_exporter.export_json_report.assert_called_once_with(output_path)

    def test_export_json_report_raises_custom_error(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        error_msg = f"error_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_json_report.side_effect = Exception(error_msg)

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        with self.assertRaises(AuditExporterError) as ctx:
            exporter.export_json_report(output_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.html"
        expected_result = f"path_html_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_html_report.return_value = expected_result

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        result = exporter.export_html_report(output_path)

        self.assertEqual(result, expected_result)
        self.mock_digest_exporter.export_html_report.assert_called_once_with(output_path)

    def test_export_html_report_raises_custom_error(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.html"
        error_msg = f"error_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_html_report.side_effect = Exception(error_msg)

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        with self.assertRaises(AuditExporterError) as ctx:
            exporter.export_html_report(output_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        stream_id = uuid.uuid4().hex
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        expected_result = f"stream_path_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_stream_to_json.return_value = expected_result

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        result = exporter.export_stream_to_json(stream_id, output_path)

        self.assertEqual(result, expected_result)
        self.mock_digest_exporter.export_stream_to_json.assert_called_once_with(stream_id, output_path)

    def test_export_stream_to_json_raises_custom_error(self):
        stream_id = uuid.uuid4().hex
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        error_msg = f"error_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_stream_to_json.side_effect = Exception(error_msg)

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        with self.assertRaises(AuditExporterError) as ctx:
            exporter.export_stream_to_json(stream_id, output_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_export_audit_report_with_exporter_custom_method(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.report"
        expected_result = f"audit_report_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_audit_report = MagicMock(return_value=expected_result)

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        result = exporter.export_audit_report(output_path)

        self.assertEqual(result, expected_result)
        self.mock_digest_exporter.export_audit_report.assert_called_once_with(output_path)

    def test_export_audit_report_fallback_to_json(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        expected_result = f"fallback_json_{uuid.uuid4().hex}"

        if hasattr(self.mock_digest_exporter, "export_audit_report"):
            del self.mock_digest_exporter.export_audit_report

        self.mock_digest_exporter.export_json_report.return_value = expected_result

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        result = exporter.export_audit_report(output_path)

        self.assertEqual(result, expected_result)
        self.mock_digest_exporter.export_json_report.assert_called_once_with(output_path)

    def test_export_audit_report_raises_custom_error(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.report"
        error_msg = f"error_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_audit_report = MagicMock(side_effect=Exception(error_msg))

        exporter = AuditExporter(
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

        with self.assertRaises(AuditExporterError) as ctx:
            exporter.export_audit_report(output_path)

        self.assertIn(error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()