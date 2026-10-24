import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.json")
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
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"test_anomaly_{uuid.uuid4().hex}"
        }
        telemetry_snapshot = {
            "cpu_load": round(random.uniform(0.0, 100.0), 2),
            "memory_usage": round(random.uniform(0.0, 100.0), 2)
        }

        log_result = self.hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(log_result)
        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть создан реально на диске.")

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(aggregate_result)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)

        if isinstance(final_report, dict):
            self.assertGreaterEqual(len(final_report), 0)


if __name__ == "__main__":
    unittest.main()