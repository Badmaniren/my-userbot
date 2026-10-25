import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"audit_log_{uuid.uuid4()}.json")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_workflow(self):
        source_name = f"service_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(500, 599),
            "description": f"Integration test error {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertIsNotNone(log_result, "Метод log_anomaly не должен возвращать None")

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result, "Метод aggregate_and_report не должен возвращать None")

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report, "Метод generate_final_report не должен возвращать None")

        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть создан в процессе работы модулей")

        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(source_name, content, "Лог должен содержать имя источника аномалии")
            self.assertIn(metric_name, content, "Отчет должен содержать имя метрики")


if __name__ == "__main__":
    unittest.main()