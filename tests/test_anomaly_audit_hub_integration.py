import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_file = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.log")

        self.threshold = round(random.uniform(0.1, 0.9), 2)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_audit_pipeline(self):
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        selected_severity = random.choice(severity_levels)

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random failure event {uuid.uuid4()}"
        }
        telemetry = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 95.0), 2)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=selected_severity,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционный сбой: лог-файл не был создан реальным AnomalyLogger."
        )

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result, "Агрегация вернула None, ожидался реальный отчет.")

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report, "Генерация финального отчета безопасности вернула None.")


if __name__ == "__main__":
    unittest.main()