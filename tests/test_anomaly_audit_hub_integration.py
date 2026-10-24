import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_audit_lifecycle_integration(self):
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly detail {uuid.uuid4()}"
        }

        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 2),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционная ошибка: Файл логов не был создан реальным AnomalyLogger."
        )

        aggregate_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(final_report, "Финальный отчет не должен быть None")

        if isinstance(final_report, dict):
            self.assertTrue(len(final_report) > 0, "Словарь финального отчета пуст")
        elif isinstance(final_report, str):
            self.assertTrue(len(final_report) > 0, "Строка финального отчета пуста")
            self.assertIn(metric_name, final_report, "Отчет должен содержать агрегированную метрику")


if __name__ == "__main__":
    unittest.main()