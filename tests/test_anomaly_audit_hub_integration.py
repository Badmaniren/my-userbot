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

    def test_log_anomaly_and_aggregation_integration(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_key = f"latency_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(10.0, 500.0), 2)

        details = {
            "error_code": random.randint(500, 599),
            "description": f"Integration test anomaly {uuid.uuid4()}"
        }
        telemetry = {
            "cpu_usage": round(random.uniform(20.0, 99.9), 2),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.assertIsInstance(log_result, dict)
        self.assertTrue(os.path.exists(self.log_file))

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_key,
            value=metric_value
        )
        self.assertIsNotNone(agg_result)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)


if __name__ == "__main__":
    unittest.main()