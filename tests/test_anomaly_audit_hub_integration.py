import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_audit_hub_integration_workflow(self):
        source_id = f"source_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_data = {"error_code": random.randint(1000, 9999), "message": str(uuid.uuid4())}
        telemetry_snapshot = {"cpu_usage": round(random.uniform(0.0, 100.0), 2), "memory": random.randint(256, 4096)}

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_data,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Файл логов должен быть создан реальным вызовом AnomalyLogger через AnomalyAuditHub."
        )

        metric_name = f"metric_{uuid.uuid4()}"
        metric_value = round(random.uniform(0.0, 10.0), 2)

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(aggregate_result, "Результат агрегации не должен быть пустым.")

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report, "Финальный отчет должен быть сгенерирован успешно.")


if __name__ == "__main__":
    unittest.main()