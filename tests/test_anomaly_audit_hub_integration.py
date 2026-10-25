import unittest
import os
import tempfile
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

    def test_anomaly_audit_hub_workflow(self):
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly occurrence {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.0), 1),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsInstance(log_result, dict)
        if "status" in log_result:
            self.assertEqual(log_result["status"], "logged")
            self.assertEqual(log_result["source"], source_id)

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsInstance(aggregate_result, dict)
        if "metric_status" in aggregate_result:
            self.assertEqual(aggregate_result["metric_status"], "reported")
            self.assertEqual(aggregate_result["metric_name"], metric_name)
            self.assertEqual(aggregate_result["value"], metric_value)

        final_report_result = self.hub.generate_final_report()
        self.assertIsInstance(final_report_result, dict)

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционный тест провален: файл логов не был создан реальным модулем AnomalyLogger."
        )

        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(source_id, log_content, "Случайный источник аномалии отсутствует в лог-файле.")


if __name__ == "__main__":
    unittest.main()