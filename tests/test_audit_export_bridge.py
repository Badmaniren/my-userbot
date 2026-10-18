import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.audit_export_bridge import AuditExportBridge, AuditExportBridgeError


class TestAuditExportBridge(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 9.9), 2)

        self.mock_audit_hub = MagicMock()
        self.mock_digest_exporter = MagicMock()

        self.bridge = AuditExportBridge(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            audit_hub=self.mock_audit_hub,
            digest_exporter=self.mock_digest_exporter
        )

    def test_init_creates_default_components(self):
        with patch("skills.audit_export_bridge.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.audit_export_bridge.DigestExporter") as mock_exporter_cls:

            inst_repo = f"/repo/{uuid.uuid4().hex}"
            inst_log = f"/logs/{uuid.uuid4().hex}.log"
            inst_threshold = round(random.uniform(1.0, 5.0), 2)

            bridge = AuditExportBridge(
                repo_path=inst_repo,
                log_path=inst_log,
                threshold=inst_threshold
            )

            mock_hub_cls.assert_called_once_with(
                repo_path=inst_repo,
                log_path=inst_log,
                threshold=inst_threshold
            )
            mock_exporter_cls.assert_called_once()
            self.assertIsNotNone(bridge.audit_hub)
            self.assertIsNotNone(bridge.digest_exporter)

    def test_export_audit_report_json_success(self):
        output_path = f"/exports/{uuid.uuid4().hex}.json"
        expected_result = f"/exports/{uuid.uuid4().hex}.json"
        self.mock_digest_exporter.export_to_json.return_value = expected_result

        result = self.bridge.export_audit_report_json(output_path)

        self.mock_digest_exporter.export_to_json.assert_called_once_with(output_path)
        self.assertEqual(result, expected_result)

    def test_export_audit_report_json_failure(self):
        output_path = f"/exports/{uuid.uuid4().hex}.json"
        error_msg = f"error_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_to_json.side_effect = Exception(error_msg)

        with self.assertRaises(AuditExportBridgeError) as ctx:
            self.bridge.export_audit_report_json(output_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_export_audit_report_html_success(self):
        output_path = f"/exports/{uuid.uuid4().hex}.html"
        expected_result = f"/exports/{uuid.uuid4().hex}.html"
        self.mock_digest_exporter.export_to_html.return_value = expected_result

        result = self.bridge.export_audit_report_html(output_path)

        self.mock_digest_exporter.export_to_html.assert_called_once_with(output_path)
        self.assertEqual(result, expected_result)

    def test_export_audit_report_html_failure(self):
        output_path = f"/exports/{uuid.uuid4().hex}.html"
        error_msg = f"error_{uuid.uuid4().hex}"
        self.mock_digest_exporter.export_to_html.side_effect = Exception(error_msg)

        with self.assertRaises(AuditExportBridgeError) as ctx:
            self.bridge.export_audit_report_html(output_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_export_audit_report_with_export_method(self):
        output_path = f"/exports/{uuid.uuid4().hex}.report"
        expected_result = f"/exports/{uuid.uuid4().hex}.report"

        del self.mock_digest_exporter.export_to_json
        self.mock_digest_exporter.export = MagicMock(return_value=expected_result)

        result = self.bridge.export_audit_report(output_path)

        self.mock_digest_exporter.export.assert_called_once_with(output_path)
        self.assertEqual(result, expected_result)

    def test_export_audit_report_fallback_to_json(self):
        output_path = f"/exports/{uuid.uuid4().hex}.json"
        path_str_result = f"/exports/{uuid.uuid4().hex}.json"

        self.mock_digest_exporter.export_to_json.return_value = path_str_result

        result = self.bridge.export_audit_report(output_path)

        self.mock_digest_exporter.export_to_json.assert_called_once_with(output_path)
        self.assertEqual(result, path_str_result)

    def test_export_audit_report_fallback_to_audit_hub_generation(self):
        output_path = f"/exports/{uuid.uuid4().hex}.json"
        json_content_str = '{' + f'"{uuid.uuid4().hex}": "{uuid.uuid4().hex}"' + '}'
        self.mock_digest_exporter.export_to_json.return_value = json_content_str

        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_audit_hub.generate_final_report.return_value = report_data

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("json.dump") as mock_json_dump:

            result = self.bridge.export_audit_report(output_path)

            mock_file.assert_called_once_with(output_path, "w", encoding="utf-8")
            mock_json_dump.assert_called_once_with(report_data, mock_file.return_value, ensure_ascii=False, indent=4)
            self.assertEqual(result, output_path)

    def test_export_audit_report_integration_failure(self):
        output_path = f"/exports/{uuid.uuid4().hex}.json"
        error_msg = f"fatal_error_{uuid.uuid4().hex}"

        if hasattr(self.mock_digest_exporter, "export"):
            del self.mock_digest_exporter.export
        self.mock_digest_exporter.export_to_json.side_effect = Exception(error_msg)
        self.mock_audit_hub.generate_final_report.side_effect = Exception(error_msg)

        with self.assertRaises(AuditExportBridgeError) as ctx:
            self.bridge.export_audit_report(output_path)

        self.assertIn("Integration export failed", str(ctx.exception))
        self.assertIn(error_msg, str(ctx.exception))

    def test_record_anomaly(self):
        source = f"src_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(1, 100)}

        self.bridge.record_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.mock_audit_hub.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def test_aggregate_metric(self):
        metric_name = f"metric_{uuid.uuid4().hex}"
        value = round(random.uniform(0.0, 1000.0), 2)

        self.bridge.aggregate_metric(
            metric_name=metric_name,
            value=value
        )

        self.mock_audit_hub.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )

    def test_generate_final_report(self):
        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "metrics": [random.randint(1, 50) for _ in range(3)]
        }
        self.mock_audit_hub.generate_final_report.return_value = expected_report

        result = self.bridge.generate_final_report()

        self.mock_audit_hub.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)