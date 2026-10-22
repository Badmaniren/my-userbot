import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_exporter import AnomalyAuditExporter, AnomalyAuditExporterError


class TestAnomalyAuditExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 9.9), 2)

        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub") as self.mock_hub_cls, \
             patch("skills.anomaly_audit_exporter.AnomalyVisualizer") as self.mock_vis_cls, \
             patch("skills.anomaly_audit_exporter.DigestExporter") as self.mock_exporter_cls:

            self.mock_hub_instance = self.mock_hub_cls.return_value
            self.mock_vis_instance = self.mock_vis_cls.return_value
            self.mock_exporter_instance = self.mock_exporter_cls.return_value

            self.exporter = AnomalyAuditExporter(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_init_initialization(self):
        self.mock_hub_cls.assert_called_once_with(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.mock_exporter_cls.assert_called_once_with(
            stability_digest=self.mock_hub_instance,
            anomaly_visualizer=self.mock_vis_instance
        )
        self.assertEqual(self.exporter.repo_path, self.repo_path)
        self.assertEqual(self.exporter.log_path, self.log_path)
        self.assertEqual(self.exporter.threshold, self.threshold)

    def test_aggregate_and_export_json_success(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        value = random.randint(100, 999)
        json_path = f"/data/{uuid.uuid4().hex}.json"
        expected_result = f"/output/{uuid.uuid4().hex}.json"

        self.mock_exporter_instance.export_json_report.return_value = expected_result

        result = self.exporter.aggregate_and_export_json(metric_name, value, json_path)

        self.mock_hub_instance.aggregate_and_report.assert_called_once_with(metric_name, value)
        self.mock_hub_instance.generate_final_report.assert_called_once()
        self.mock_exporter_instance.export_json_report.assert_called_once_with(json_path)
        self.assertEqual(result, expected_result)

    def test_aggregate_and_export_json_exception_handling(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        value = random.random()
        json_path = f"/data/{uuid.uuid4().hex}.json"
        error_message = uuid.uuid4().hex

        self.mock_hub_instance.aggregate_and_report.side_effect = Exception(error_message)

        with self.assertRaises(AnomalyAuditExporterError) as ctx:
            self.exporter.aggregate_and_export_json(metric_name, value, json_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_export_html_success(self):
        html_path = f"/var/www/{uuid.uuid4().hex}.html"
        expected_result = f"/var/www/rendered_{uuid.uuid4().hex}.html"

        self.mock_exporter_instance.export_html_report.return_value = expected_result

        result = self.exporter.export_html(html_path)

        self.mock_exporter_instance.export_html_report.assert_called_once_with(html_path)
        self.assertEqual(result, expected_result)

    def test_export_html_exception_handling(self):
        html_path = f"/var/www/{uuid.uuid4().hex}.html"
        error_message = uuid.uuid4().hex

        self.mock_exporter_instance.export_html_report.side_effect = Exception(error_message)

        with self.assertRaises(AnomalyAuditExporterError) as ctx:
            self.exporter.export_html(html_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_export_audit_report_success(self):
        output_path = f"/reports/{uuid.uuid4().hex}.json"
        expected_result = f"/reports/final_{uuid.uuid4().hex}.json"

        self.mock_exporter_instance.export_json_report.return_value = expected_result

        result = self.exporter.export_audit_report(output_path)

        self.mock_hub_instance.generate_final_report.assert_called_once()
        self.mock_exporter_instance.export_json_report.assert_called_once_with(output_path)
        self.assertEqual(result, expected_result)

    def test_export_audit_report_exception_handling(self):
        output_path = f"/reports/{uuid.uuid4().hex}.json"
        error_message = uuid.uuid4().hex

        self.mock_hub_instance.generate_final_report.side_effect = Exception(error_message)

        with self.assertRaises(AnomalyAuditExporterError) as ctx:
            self.exporter.export_audit_report(output_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_log_external_anomaly_success(self):
        source = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"info": uuid.uuid4().hex, "code": random.randint(1, 500)}
        telemetry_snapshot = {"cpu": random.uniform(10.0, 99.9), "mem": random.randint(1000, 8000)}

        self.exporter.log_external_anomaly(source, severity, details, telemetry_snapshot)

        self.mock_hub_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def test_log_external_anomaly_exception_handling(self):
        source = uuid.uuid4().hex
        severity = random.choice(["INFO", "WARNING", "FATAL"])
        details = uuid.uuid4().hex
        telemetry_snapshot = {"uptime": random.randint(100, 99999)}
        error_message = uuid.uuid4().hex

        self.mock_hub_instance.log_anomaly.side_effect = Exception(error_message)

        with self.assertRaises(AnomalyAuditExporterError) as ctx:
            self.exporter.log_external_anomaly(source, severity, details, telemetry_snapshot)

        self.assertIn(error_message, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()