import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"anomaly_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.test_dir
        self.threshold = random.uniform(50.0, 95.0)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_audit_and_aggregation_pipeline(self):
        unique_source = f"source_{uuid.uuid4().hex[:8]}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        selected_severity = random.choice(severities)

        random_metric_val = round(random.uniform(0.0, 100.0), 2)
        random_metric_name = f"metric_{uuid.uuid4().hex[:6]}"

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly message {uuid.uuid4()}"
        }
        telemetry = {
            "cpu_load": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.audit_hub.log_anomaly(
            source=unique_source,
            severity=selected_severity,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.assertTrue(
            os.path.exists(self.log_path),
            "Интеграционная ошибка: логгер не создал файл отчета на диске."
        )

        agg_result = self.audit_hub.aggregate_and_report(
            metric_name=random_metric_name,
            value=random_metric_val
        )

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(final_report, "Финальный отчет не должен быть пустым.")

        logged_anomalies = self.audit_hub.logger.get_anomalies()
        found = False
        for anomaly in logged_anomalies:
            if anomaly.get("source") == unique_source and anomaly.get("severity") == selected_severity:
                found = True
                self.assertEqual(anomaly["details"]["error_code"], details["error_code"])
                break

        self.assertTrue(found, "Записанная аномалия не найдена через связанный логгер.")

if __name__ == "__main__":
    unittest.main()