import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_file = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.json")
        self.threshold = round(random.uniform(0.1, 9.9), 2)
        
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_anomaly_audit_flow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        selected_severity = random.choice(severity_levels)
        
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Test anomaly message {uuid.uuid4().hex}"
        }
        telemetry_snapshot = {
            "cpu_load": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=selected_severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        
        self.assertIsNotNone(log_result, "Log anomaly method should return a result without swallowing exceptions.")

        aggregate_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(aggregate_result, "Aggregate and report method should process the metric.")

        final_report = self.hub.generate_final_report()
        self.assertIsInstance(final_report, (dict, list, str), "Final report should return structured output.")

        self.assertTrue(os.path.exists(self.log_file), "The audit log file must be physically created on disk.")


if __name__ == "__main__":
    unittest.main()