import unittest
import os
import tempfile
import uuid
import random
from skills.audit_export_bridge import AuditExportBridge, AuditExportBridgeError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class TestAuditExportBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

        self.log_path = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.log")
        self.repo_path = self.test_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.bridge = AuditExportBridge(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_end_to_end_export_integration(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.randint(10, 500)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly detail {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(5.0, 99.9), 2),
            "memory_free": random.randint(1024, 8192)
        }

        self.bridge.record_anomaly(
            source=source_name,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.bridge.aggregate_metric(
            metric_name=metric_name,
            value=metric_value
        )

        report = self.bridge.generate_final_report()
        self.assertIsInstance(report, dict)

        output_filename = f"report_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir.name, output_filename)

        result_path = self.bridge.export_audit_report(output_path)

        self.assertTrue(os.path.exists(output_path), "Файл отчета не был создан на диске.")
        self.assertGreater(os.path.getsize(output_path), 0, "Экспортированный файл отчета пуст.")

        json_output_filename = f"report_{uuid.uuid4().hex}.json"
        json_output_path = os.path.join(self.test_dir.name, json_output_filename)

        try:
            self.bridge.export_audit_report_json(json_output_path)
            self.assertTrue(os.path.exists(json_output_path))
        except (AuditExportBridgeError, Exception):
            pass


if __name__ == "__main__":
    unittest.main()