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
        self.log_file = os.path.join(self.test_dir, f"anomaly_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.test_dir
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_anomaly_pipeline(self):
        source_id = f"service_{uuid.uuid4().hex[:6]}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity = random.choice(severities)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly failure {uuid.uuid4().hex}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 2),
            "memory_free": random.randint(1024, 16384)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть создан при фиксации аномалии")

        metric_name = f"latency_{uuid.uuid4().hex[:4]}"
        metric_value = round(random.uniform(0.0, 1.5), 4)

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(aggregate_result)

        final_report = self.hub.generate_final_report()
        self.assertIsInstance(final_report, (dict, list, str))

        logs_data = self.hub.logger.get_anomalies()
        found = False
        for entry in logs_data:
            if entry.get("source") == source_id and entry.get("details", {}).get("error_code") == details["error_code"]:
                found = True
                break

        self.assertTrue(found, "Записанная аномалия должна успешно читаться через встроенный логгер без моков")


if __name__ == "__main__":
    unittest.main()