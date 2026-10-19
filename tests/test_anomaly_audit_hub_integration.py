import unittest
import tempfile
import os
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

    def test_anomaly_audit_hub_workflow(self):
        source_id = f"source_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4()}"
        metric_value = round(random.uniform(0.0, 100.0), 2)
        
        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly message {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 90.0), 2)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        
        self.assertIsNotNone(log_result)
        self.assertTrue(os.path.exists(self.log_file))

        aggregation_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(aggregation_result)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)


if __name__ == "__main__":
    unittest.main()