import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_audit_hub_full_integration_flow(self):
        source_id = f"source_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4()}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details_data = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random failure description {uuid.uuid4()}"
        }

        telemetry_snapshot_data = {
            "cpu_load": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 90.0), 1)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_data,
            telemetry_snapshot=telemetry_snapshot_data
        )

        self.assertIsNotNone(log_result, "Метод log_anomaly должен возвращать результат логирования")

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(aggregate_result, "Метод aggregate_and_report должен обрабатывать метрику")

        final_report = self.hub.generate_final_report()

        self.assertIsNotNone(final_report, "Метод generate_final_report должен возвращать итоговый отчет")

        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть физически создан в системе")


if __name__ == "__main__":
    unittest.main()