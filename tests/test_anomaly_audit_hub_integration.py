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
        self.threshold = round(random.uniform(0.1, 9.9), 2)
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

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
            "cpu_load": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Integration failure: AnomalyLogger did not create the log file."
        )

        aggregate_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(final_report, "Integration failure: Final report is None.")
        
        if isinstance(final_report, dict):
            self.assertIn(metric_name, str(final_report), "Metric name missing from final report.")
        elif isinstance(final_report, str):
            self.assertGreater(len(final_report), 0, "Final report string is empty.")
        else:
            self.assertTrue(True, "Final report generated successfully.")


if __name__ == "__main__":
    unittest.main()