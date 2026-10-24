import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"test_log_{uuid.uuid4()}.json")
        self.repo_path = self.test_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_audit_lifecycle_integration(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        selected_severity = random.choice(severities)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random failure event {uuid.uuid4()}"
        }

        telemetry = {
            "cpu_usage": round(random.uniform(50.0, 99.9), 2),
            "memory_free": random.randint(1024, 16384)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=selected_severity,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть создан в процессе логирования аномалии.")

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.hub.generate_final_report()

        self.assertIsNotNone(final_report, "Финальный отчет не должен быть пустым.")
        self.assertIsInstance(final_report, (dict, str, list), "Финальный отчет должен иметь корректный тип данных.")


if __name__ == "__main__":
    unittest.main()