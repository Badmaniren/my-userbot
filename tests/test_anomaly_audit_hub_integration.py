import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"anomaly_log_{uuid.uuid4()}.json")
        self.repo_path = self.test_dir.name
        self.threshold = round(random.uniform(0.5, 5.0), 2)
        
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_log_anomaly_and_aggregation_workflow(self):
        source_id = f"service_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4()}"
        metric_value = round(random.uniform(0.0, 10.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random error details {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 90.0), 2)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertIsNotNone(log_result)

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)
        self.assertTrue(os.path.exists(self.log_file))


if __name__ == "__main__":
    unittest.main()