import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"audit_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.test_dir.name
        self.threshold = round(random.uniform(0.5, 99.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_audit_pipeline(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        unique_detail_key = f"key_{uuid.uuid4().hex[:6]}"
        unique_detail_val = random.randint(1000, 9999)
        details = {unique_detail_key: unique_detail_val}

        telemetry_key = f"cpu_{uuid.uuid4().hex[:4]}"
        telemetry_snapshot = {telemetry_key: round(random.uniform(10.0, 99.9), 2)}

        log_result = self.hub.log_anomaly(
            source=source_name,
            severity=chosen_severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(log_result, "Метод log_anomaly не должен возвращать None")

        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(0.0, 150.0), 2)

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(aggregate_result, "Метод aggregate_and_report не должен возвращать None")

        final_report = self.hub.generate_final_report()

        self.assertIsNotNone(final_report, "Финальный отчет не должен быть пустым")

        self.assertTrue(
            os.path.exists(self.log_file),
            f"Файл логов {self.log_file} должен быть физически создан в процессе работы конвейера"
        )

        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(source_name, log_content, "Лог должен содержать уникальное имя источника аномалии")
            self.assertIn(str(unique_detail_val), log_content, "Лог должен содержать детали аномалии")


if __name__ == "__main__":
    unittest.main()