import unittest
import os
import tempfile
import uuid
import random
from skills.audit_exporter import AuditExporter
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter

class TestAuditExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        self.audit_exporter = AuditExporter(audit_hub=self.audit_hub)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_audit_export(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = round(random.uniform(10.0, 500.0), 2)

        details_msg = f"Random anomaly detail UUID: {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.randint(1, 100), "memory_usage": random.randint(100, 2048)}

        self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        self.audit_hub.aggregate_and_report(
            metric_name=metric_key,
            value=metric_val
        )

        output_filename = f"report_{uuid.uuid4()}.json"
        output_path = os.path.join(self.repo_path, output_filename)

        exported_path = self.audit_exporter.export_audit_report(output_path=output_path)

        self.assertTrue(os.path.exists(exported_path), "Экспортированный файл отчета аудита должен реально существовать в файловой системе.")

        with open(exported_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(source_id, content, "Отчет должен содержать уникальный идентификатор источника аномалии.")
            self.assertIn(details_msg, content, "Отчет должен содержать детали аномалии.")
            self.assertIn(metric_key, content, "Отчет должен содержать агрегированное имя метрики.")

if __name__ == "__main__":
    unittest.main()