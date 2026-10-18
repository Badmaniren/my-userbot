import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
from pathlib import Path

from skills.anomaly_audit_exporter import AnomalyAuditExporter

class TestAnomalyAuditExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 10.0)

        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub") as mock_hub, \
             patch("skills.anomaly_audit_exporter.AnomalyLogger") as mock_logger:

            self.mock_hub_instance = mock_hub.return_value
            self.mock_logger_instance = mock_logger.return_value
            self.exporter = AnomalyAuditExporter(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_initialization_composes_correctly(self):
        rand_repo = f"/var/repo/{uuid.uuid4().hex}"
        rand_log = f"/var/log/{uuid.uuid4().hex}.log"
        rand_threshold = random.uniform(1.0, 100.0)

        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.anomaly_audit_exporter.AnomalyLogger") as mock_logger_cls:

            exporter = AnomalyAuditExporter(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_threshold
            )

            mock_hub_cls.assert_called_once_with(repo_path=rand_repo, log_path=rand_log, threshold=rand_threshold)
            mock_logger_cls.assert_called_once_with(log_path=rand_log)
            self.assertEqual(exporter.repo_path, rand_repo)
            self.assertEqual(exporter.log_path, rand_log)

    def test_export_audit_log_success(self):
        rand_content = "".join(random.choices(string.ascii_letters + string.digits, k=64))
        mock_file_data = io.BytesIO(rand_content.encode('utf-8'))

        self.mock_logger_instance.get_structured_report.return_value = {
            "status": "success",
            "data": rand_content
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            destination = f"/export/{uuid.uuid4().hex}.json"
            result = self.exporter.export_audit_log(destination)

            self.mock_logger_instance.get_structured_report.assert_called_once()
            mock_file.assert_called_once_with(destination, 'w', encoding='utf-8')
            self.assertTrue(result)

    def test_log_and_audit_anomaly_delegates(self):
        source = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(1000, 9999), "message": uuid.uuid4().hex}
        telemetry = {"cpu_load": random.random(), "memory": random.randint(100, 500)}

        self.exporter.log_and_audit_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.mock_hub_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )
        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )

    def test_aggregate_metrics_and_report(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(10.0, 500.0)

        expected_report = {
            "metric": metric_name,
            "aggregated_value": metric_value,
            "uuid": uuid.uuid4().hex
        }
        self.mock_hub_instance.aggregate_and_report.return_value = expected_report

        res = self.exporter.aggregate_metrics_and_report(metric_name, metric_value)

        self.mock_hub_instance.aggregate_and_report.assert_called_once_with(metric_name, metric_value)
        self.assertEqual(res, expected_report)

    def test_generate_final_report_passthrough(self):
        final_data = {
            "summary": uuid.uuid4().hex,
            "total_anomalies": random.randint(0, 50)
        }
        self.mock_hub_instance.generate_final_report.return_value = final_data

        report = self.exporter.generate_final_report()

        self.mock_hub_instance.generate_final_report.assert_called_once()
        self.assertEqual(report, final_data)

    def test_clear_all_logs(self):
        self.exporter.clear_all_logs()
        self.mock_logger_instance.clear_logs.assert_called_once()

    def test_export_audit_log_io_error_handling(self):
        self.mock_logger_instance.get_structured_report.return_value = {"error": None}

        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            destination = f"/invalid_path/{uuid.uuid4().hex}.json"
            result = self.exporter.export_audit_log(destination)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()